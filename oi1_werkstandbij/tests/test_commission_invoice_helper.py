# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
import datetime


@tagged('test_commission_invoice_helper')
class TestHourBookProcess(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)

		test_company_id = 1
		self.env.user.lang = False

		sale_obj = self.env['sale.order']
		product_obj = self.env['product.template']
		partner_obj = self.env['res.partner']
		commission_obj = self.env['oi1_commission']
		payment_term_obj = self.env['account.payment.term']
		free_worker_obj = self.env['oi1_free_worker']
		account_analytic_line_obj = self.env['account.analytic.line']
		sale_order_line_obj = self.env['sale.order.line']

		self.mediator_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_mediator')
		self.company_id = self.env['res.company'].browse([test_company_id])
		payment_term = payment_term_obj.search([('company_id', 'in', (self.company_id.id, False))])[0]

		self.free_worker = free_worker_obj.create({'x_name': 'test freeworker'})

		self.product = product_obj.create({'name': 'test_product'})
		self.com_product = product_obj.create({'name': 'com_product'})
		self.commission = commission_obj.create(
			{'name': 'test commission', 'product_id': self.com_product.product_variant_id.id})
		
		self.customer = partner_obj.create({'name': ' test work provider'})
		self.com_partner = partner_obj.create({'name': ' test commission receiver'})
		self.sale_order = sale_obj.create({'partner_id': self.customer.id,
										   'payment_term_id': payment_term.id})

		self.sale_order_line = sale_order_line_obj.create({'order_id': self.sale_order.id,
														   'product_id' : self.env.ref('oi1_werkstandbij.product_template_free_workers_poule').id
														   })
		self.sale_order.action_confirm()

		self.hour_line = account_analytic_line_obj.create({
			'x_partner_id': self.free_worker.partner_id.id,
			'x_sale_id': self.sale_order.id,
			'x_from_time': "08:00",
			'x_to_time': "17:00",
			'x_pause_time': "02:00",
			'project_id': self.sale_order_line.project_id.id,
			'unit_amount': 7.0,
			'x_rate': 15.00
		})
		return result

	def test_get_commissions_on_analytic_hour_worker(self):
		commission_obj = self.env['oi1_commission']
		commission_partner_obj = self.env['oi1_commission_partner']
		commission_payment_obj = self.env['oi1_sale_commission_payment']
		invoice_helper_obj = self.env['oi1_commission_invoice_helper']
		product_product_obj = self.env['product.product']
		partner_obj = self.env['res.partner']

		c_default_rate = 0.12
		c_amount = c_default_rate * self.hour_line.unit_amount

		partner1 = partner_obj.create({'name':'test_commission'})

		#2021_0406 test with empty commissions
		commission_payment_lines = invoice_helper_obj.set_commission_payment_lines_customer(self.hour_line)



		product_id = product_product_obj.create({'name': 'commission_product'})
		commission_mediator = commission_obj.create({'name': self.mediator_role.name,
													 'commission_role_id': self.mediator_role.id,
													 'product_id': product_id.id,
													 'default_rate': c_default_rate
													 })
		commission_partner = commission_partner_obj.create({'partner_id': partner1.id,
															'commission_id': commission_mediator.id})
		self.free_worker.mediator_partner_id = partner1
		# Partner1 should be hte mediator of the freeworker
		self.assertEqual(self.free_worker.mediator_partner_id.id, partner1.id)

		# 2021_0406 test with 1 commissions
		invoice_helper_obj.do_create_commissions(self.hour_line)

		commission_payment = commission_payment_obj.search([('partner_id','=', partner1.id)])
		# 2021_0622 The commission is not generated because there are payment lines already generated on the hourline
		self.assertEqual(len(commission_payment), 0)

		commission_payment_lines.unlink()
		invoice_helper_obj.do_create_commissions(self.hour_line)

		commission_payment = commission_payment_obj.search([('partner_id', '=', partner1.id)])
		# 2021_0622 The commission generated because there payment lines already generated on the hourline
		self.assertEqual(len(commission_payment), 1)
		self.assertEqual(commission_payment.amount, c_amount)

		#2021_0406 test with already processed commissions which shouldn't have an effect.
		self.hour_line.write({'system': 1, 'x_commission_created': True})
		invoice_helper_obj.do_create_commissions(self.hour_line)
		self.assertEqual(len(commission_payment), 1)
		self.assertEqual(commission_payment.amount, c_amount)

	def test_commission_within_sub_commissions_and_saller_role(self):
		commission_obj = self.env['oi1_commission']
		commission_payment_obj = self.env['oi1_sale_commission_payment']
		commission_payment_line_obj = self.env['oi1_sale_commission_payment_line']
		commission_partner_obj = self.env['oi1_commission_partner']
		commission_role_obj = self.env['oi1_commission_role']
		invoice_helper_obj = self.env['oi1_commission_invoice_helper']
		partner_obj = self.env['res.partner']
		product_product_obj = self.env['product.product']

		c_default_rate = 2.5
		c_sub_commission_rate = 1.5
		c_amount = c_default_rate * self.hour_line.unit_amount
		c_current_date = datetime.date.today()

		seller_role = commission_role_obj.get_seller_role()
		self.assertTrue(seller_role)


		partner1 = partner_obj.create({'name': 'test_rate_list partner'})
		self.assertTrue(partner1.id)
		product_id = product_product_obj.create({'name': 'commission_product'})
		self.assertTrue(product_id.id)

		commission_seller = commission_obj.create({'name': self.mediator_role.name,
													 'commission_role_id': seller_role.id,
													 'product_id': product_id.id,
													 'default_rate': c_default_rate
													 })
		sub_commission = commission_obj.create({'name': 'test_commission', 'default_rate': c_sub_commission_rate,
												'product_id': product_id.id})
		self.assertTrue(sub_commission.id)

		self.assertEqual(commission_seller.get_compute_calculation_rate(10, c_current_date), c_default_rate)
		self.assertEqual(commission_seller.commission_role_id.id,seller_role.id)
		self.assertTrue(commission_seller.id)

		commission_partner = commission_partner_obj.create({'partner_id': partner1.id,
															'commission_id': commission_seller.id})

		self.assertEqual(commission_partner.commission_role_id.id, seller_role.id)
		self.assertEqual(commission_partner.commission_id.id, commission_seller.id)
		self.assertTrue(commission_partner.id)
		self.assertFalse(partner1.x_is_operational_work_planner)
		self.assertTrue(partner1.x_is_seller)

		self.sale_order_line.order_id.x_seller_partner_id = partner1
		self.assertEqual(self.sale_order_line.order_id.x_seller_partner_id.id,
						  partner1.id)

		commission_payment_lines = invoice_helper_obj.set_commission_payment_lines_customer(self.hour_line)

		commission_payment = commission_payment_obj.search([('partner_id', '=', partner1.id)])
		# 2021_0622 The commission generated because there payment lines already generated on the hourline
		self.assertEqual(len(commission_payment), 1)
		self.assertEqual(commission_payment.amount, c_amount)
		commission_pay_lines = commission_payment_line_obj.search(
			[('commission_payment_log_id', 'in', commission_payment_lines.ids)])
		commission_pay_lines.unlink()
		commission_payment_lines.unlink()

		commission_seller.write({"sub_commission_ids": [(6, 0, [sub_commission.id])]})
		commission_payment_lines = invoice_helper_obj.set_commission_payment_lines_customer(self.hour_line)

		commission_payment = commission_payment_obj.search([('partner_id', '=', partner1.id)])
		# 2021_0622 The commission generated because there payment lines already generated on the hourline
		self.assertEqual(len(commission_payment), 1)
		self.assertEqual(commission_payment.amount, c_amount)

		commission_payment_logs = invoice_helper_obj.get_commission_payment_logs(self.hour_line)
		sub_commission_payment_logs = commission_payment_logs.filtered(lambda l: l.is_sub_commission)
		self.assertTrue(sub_commission in sub_commission_payment_logs.commission_id)

	def test_set_commission_with_rate_list_and_operational_work_planner(self):
		commission_obj = self.env['oi1_commission']
		commission_partner_obj = self.env['oi1_commission_partner']
		commission_payment_obj = self.env['oi1_sale_commission_payment']
		commission_payment_line_obj = self.env['oi1_sale_commission_payment_line']
		commission_rate_list_obj = self.env['oi1_commission_rate_list']
		commission_rate_list_line_obj = self.env['oi1_commission_rate_list_line']
		commission_role_obj = self.env['oi1_commission_role']
		invoice_helper_obj = self.env['oi1_commission_invoice_helper']
		partner_obj = self.env['res.partner']
		product_product_obj = self.env['product.product']

		c_default_rate = 1.0
		c_amount = c_default_rate * self.hour_line.unit_amount
		c_current_date = datetime.date.today()

		operational_work_planner_role = commission_role_obj.get_operational_work_planner_role()
		self.assertTrue(operational_work_planner_role.id)

		commission_rate_list = commission_rate_list_obj.create({'name': 'test_rate_list'})
		self.assertTrue(commission_rate_list.id)
		commission_rate_list_line = commission_rate_list_line_obj.create({'rate_list_id': commission_rate_list.id,
																		  'default_rate': 2.25,
																		  'hour_rate': 10.00})
		self.assertTrue(commission_rate_list_line.id)
		partner1 = partner_obj.create({'name': 'test_rate_list partner'})
		self.assertTrue(partner1.id)
		product_id = product_product_obj.create({'name': 'commission_product'})
		self.assertTrue(product_id.id)

		commission_mediator = commission_obj.create({'name': self.mediator_role.name,
													 'commission_role_id': operational_work_planner_role.id,
													 'product_id': product_id.id,
													 'default_rate': c_default_rate
													 })
		self.assertEqual(commission_mediator.get_compute_calculation_rate(10, c_current_date), c_default_rate)
		self.assertEqual(commission_mediator.commission_role_id.id, operational_work_planner_role.id)
		self.assertTrue(commission_mediator.id)

		commission_partner = commission_partner_obj.create({'partner_id': partner1.id,
															'commission_id': commission_mediator.id})

		self.assertEqual(commission_partner.commission_role_id.id, operational_work_planner_role.id)

		self.assertEqual(commission_partner.commission_id.id, commission_mediator.id)
		self.assertTrue(commission_partner.id)
		self.assertTrue(partner1.x_is_operational_work_planner)

		self.sale_order_line.x_poule_id.operational_work_planner_partner_id = partner1
		self.assertEqual(self.sale_order_line.x_poule_id.operational_work_planner_partner_id.id, partner1.id)

		commission_payment_lines = invoice_helper_obj.set_commission_payment_lines_customer(self.hour_line)

		commission_payment = commission_payment_obj.search([('partner_id', '=', partner1.id)])
		# 2021_0622 The commission generated because there payment lines already generated on the hourline
		self.assertEqual(len(commission_payment), 1)
		self.assertEqual(commission_payment.amount, c_amount)
		commission_pay_lines = commission_payment.sale_commission_payment_lines
		self.assertEqual(len(commission_pay_lines), 1)
		commission_logs = commission_pay_lines.commission_payment_log_id.commission_log_id
		self.assertEqual(len(commission_logs), 1)
		commission_pay_lines = commission_payment_line_obj.search([('commission_payment_log_id', 'in', commission_payment_lines.ids)])
		commission_pay_lines.unlink()
		commission_payment_lines.unlink()

		#Na Testen van een commissie nu testen van de staffel
		commission_mediator.commission_rate_list_id = commission_rate_list
		commission_logs.commission_rate_list_id = commission_rate_list

		commission_payment_lines = invoice_helper_obj.set_commission_payment_lines_customer(self.hour_line)
		commission_payment = commission_payment_obj.search([('partner_id', '=', partner1.id)])

		# 2021_0622 The commission generated because there payment lines already generated on the hourline
		self.assertEqual(len(commission_payment), 1)
		self.assertEqual(commission_payment.amount, commission_rate_list_line.default_rate * self.hour_line.unit_amount)
		commission_pay_lines = commission_payment_line_obj.search(
			[('commission_payment_log_id', 'in', commission_payment_lines.ids)])
		commission_pay_lines.unlink()
		commission_payment_lines.unlink()

		commission_rate_list_line1 = commission_rate_list_line_obj.create({'rate_list_id': commission_rate_list.id,
																		  'default_rate': 50,
																		  'hour_rate': 100.00})

		commission_payment_lines = invoice_helper_obj.set_commission_payment_lines_customer(self.hour_line)
		commission_payment = commission_payment_obj.search([('partner_id', '=', partner1.id)])
		self.assertTrue(commission_rate_list_line1.id)
		self.assertEqual(len(commission_payment), 1)
		self.assertEqual(commission_payment.amount,
						  commission_rate_list_line.default_rate * self.hour_line.unit_amount)
		commission_pay_lines = commission_payment_line_obj.search(
			[('commission_payment_log_id', 'in', commission_payment_lines.ids)])
		commission_pay_lines.unlink()
		commission_payment_lines.unlink()

		commission_rate_list_line1 = commission_rate_list_line_obj.create({'rate_list_id': commission_rate_list.id,
																		   'default_rate': 5,
																		   'hour_rate': 14.00})
		self.assertTrue(commission_rate_list_line1.id)
		commission_payment_lines = invoice_helper_obj.set_commission_payment_lines_customer(self.hour_line)
		commission_payment = commission_payment_obj.search([('partner_id', '=', partner1.id)])
		self.assertTrue(commission_rate_list_line1.id)
		self.assertEqual(len(commission_payment), 1)
		self.assertEqual(commission_payment.amount,
						  commission_rate_list_line1.default_rate * self.hour_line.unit_amount)
		commission_pay_lines = commission_payment_line_obj.search(
			[('commission_payment_log_id', 'in', commission_payment_lines.ids)])
		commission_pay_lines.unlink()
		commission_payment_lines.unlink()

	def test_set_commission_payment_line_vendor(self):
		commission_free_worker_obj = self.env['oi1_commission_free_worker']
		account_move_obj = self.env['account.move']

		c_default_rate = 2.34
		c_amount = c_default_rate * self.hour_line.unit_amount

		invoice_helper_obj = self.env['oi1_commission_invoice_helper']
		invoice_helper_obj.do_create_commissions(self.hour_line)

		self.commission.default_rate = c_default_rate
		self.assertEqual(self.commission.default_rate, c_default_rate)

		self.hour_line.write({'system': 1, 'x_commission_created': False})
		commission_free_worker = commission_free_worker_obj.create({'free_worker_id': self.free_worker.id,
																	'commission_id': self.commission.id,
																	})

		commission_logs = self.free_worker.commission_free_worker_ids
		self.assertTrue(len(commission_logs), 1)
		self.assertEqual(commission_logs.default_rate, c_default_rate)

		commission_free_worker.use_default_rate = False
		commission_free_worker.default_rate = c_default_rate
		self.assertTrue(commission_free_worker.partner_id.id)
		self.assertEqual(commission_free_worker.default_rate, c_default_rate)
		invoice_helper_obj.do_create_commissions(self.hour_line)

		self.commission.payment_by = 'freeworker'

		self.assertEqual(self.commission.payment_by, 'freeworker')

		payment_logs = invoice_helper_obj.get_commission_payment_logs(self.hour_line)
		self.assertNotEqual(len(payment_logs), 0)
		#Removed payment logs should work
		payment_logs.commission_payment_line_id.unlink()
		payment_logs.unlink()
		with self.assertRaises(UserError) as e:
				invoice_helper_obj.do_create_commissions(self.hour_line)
		self.assertIn('No valid invoice found for freeworker', str(e.exception))

		journal_id = self.env.ref('oi1_werkstandbij.workerspayment_journal')

		account_move = account_move_obj.create({'partner_id': self.free_worker.partner_id.id,
								 'move_type': 'in_invoice',
								 'journal_id': journal_id.id,
								 })

		invoice_helper_obj.do_create_commissions(self.hour_line)

		account_moves = account_move_obj.search([('partner_id', '=', self.free_worker.partner_id.id)])
		self.assertEqual(len(account_moves), 1)
		self.assertEqual(account_move.id, account_moves.id)
		self.assertEqual(-account_moves.amount_untaxed, c_amount)
		return account_moves

