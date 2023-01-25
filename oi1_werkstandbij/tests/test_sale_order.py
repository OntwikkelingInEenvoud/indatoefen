# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from datetime import date, timedelta


@tagged('post_install', 'test_sale_order')
class TestSaleOrder(TransactionCase):
	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)
		sale_obj = self.env['sale.order']
		product_obj = self.env['product.template']
		partner_obj = self.env['res.partner']
		poule_obj = self.env['oi1_freeworkerpoule']
		commission_obj = self.env['oi1_commission']
		payterm_obj = self.env['account.payment.term']

		payment_term = payterm_obj.search([('company_id','in', (self.env.company.id,False))])[0]

		self.free_worker = partner_obj.create({'name': 'test freeworker', 'x_is_freeworker': True})

		self.product = product_obj.create({'name': 'test_product'})
		self.com_product = product_obj.create({'name': 'com_product'})
		self.commission = commission_obj.create(
			{'name': 'test commission', 'product_id': self.com_product.product_variant_id.id})

		self.poule = poule_obj.create({'name': 'test poule',
									   'act_description': 'test activiteit',
									   'product_id': self.product.product_variant_id.id})
		self.customer = partner_obj.create({'name': ' test work provider'})
		self.com_partner = partner_obj.create({'name': ' test commission receiver'})
		self.sale_order = sale_obj.create({'partner_id': self.customer.id,
										   'x_poule_id': self.poule.id,
										   'payment_term_id': payment_term.id})


		return result

	"""
	2021_0629 The creation of the sales order with the creation of the poule and the project is tested.
	"""
	def test_create_sales_order(self):
		sale_obj = self.env['sale.order']
		sale_order_line_obj = self.env['sale.order.line']

		product_id = self.env.ref('oi1_werkstandbij.product_template_free_workers_poule')

		c_customer_name = 'QQQ'
		self.customer.name = c_customer_name

		sale_order = sale_obj.create({'partner_id': self.customer.id})
		sale_order_line = sale_order_line_obj.create({'order_id': sale_order.id, 'product_id': product_id.id})
		self.assertTrue(sale_order_line.id)
		sale_order.action_confirm()

		project_project = sale_order.project_ids
		self.assertEqual(len(project_project), 1)
		self.assertIn('QQQ', project_project.name)

