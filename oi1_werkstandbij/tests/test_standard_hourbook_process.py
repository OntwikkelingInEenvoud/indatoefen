# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, Form, tagged
from odoo.exceptions import UserError, ValidationError
import datetime

@tagged('test_standard_hourbook_process')
class TestHourBookProcess(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)

		test_company_id = 1
		self.env.user.lang = False
		self.seller_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_sales')

		sale_obj = self.env['sale.order']
		product_obj = self.env['product.template']
		partner_obj = self.env['res.partner']
		poule_obj = self.env['oi1_freeworkerpoule']
		commission_obj = self.env['oi1_commission']
		payment_term_obj = self.env['account.payment.term']
		free_worker_obj = self.env['oi1_free_worker']
		account_analytic_line_obj = self.env['account.analytic.line']
		sale_order_line_obj = self.env['sale.order.line']
		commission_partner_obj = self.env['oi1_commission_partner']

		self.partner_commission_seller = partner_obj.create({'name' : 'commission_seller'})

		commission_product_id = product_obj.create({'name': 'commission product id'})

		commission_seller = commission_obj.create({'name': self.seller_role.name,
												   'commission_role_id': self.seller_role.id,
												   'product_id': commission_product_id.id,
												   'default_rate': 0.10
												   })
		commission_partner_obj.create({'partner_id': self.partner_commission_seller.id,
									   'commission_id': commission_seller.id})


		self.company_id = self.env['res.company'].browse([test_company_id])
		payment_term = payment_term_obj.search([('company_id', 'in', (self.company_id.id, False))])[0]

		self.free_worker = free_worker_obj.create({'x_name': 'test freeworker'})


		self.product = product_obj.create({'name': 'test_product', 'type': 'service'})
		self.com_product = product_obj.create({'name': 'com_product'})
		self.commission = commission_obj.create(
			{'name': 'test commission', 'product_id': self.com_product.product_variant_id.id})

		poules = poule_obj.search([('name', '=', 'test poule')])
		for poule in poules:
			poule.active = False

		self.poule = poule_obj.create({'name': 'test poule',
								   'act_description': 'test activiteit',
								   'product_id': self.product.product_variant_id.id})

		self.customer = partner_obj.create({'name': ' test work provider'})
		self.com_partner = partner_obj.create({'name': ' test commission receiver'})
		self.sale_order = sale_obj.create({'partner_id': self.customer.id,
										   'x_poule_id': self.poule.id,
										   'payment_term_id': payment_term.id})
		self.sale_order.x_seller_partner_id = self.partner_commission_seller

		self.sale_order_line = sale_order_line_obj.create({'order_id': self.sale_order.id,
														   'product_id': self.product.id,
														   'x_price': 15,
														   })
		self.poule.project_id.write({'sale_line_id': self.sale_order_line,
									 'sale_order_id': self.sale_order_line.order_id.id})


		self.hour_line = account_analytic_line_obj.create({
			'x_partner_id': self.free_worker.partner_id.id,
			'x_sale_id': self.sale_order.id,
			'x_from_time': "08:00",
			'x_to_time': "17:00",
			'x_pause_time': "02:00",
			'project_id': self.poule.project_id.id,
			'unit_amount': 7.0,
			'x_rate': 15.00
		})
		return result

	def test_create_credit_invoice(self):
		account_move_obj = self.env['account.move']
		agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
		invoice_refund_hour_wizard_obj = self.env['oi1_werkstandbij.invoice_refund_hour_wizard']
		invoice_wizard_obj = self.env['oi1_werkstandbij.invoice_wizard']

		wizard = agree_hour_line_wizard_obj.create({})
		wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_agreements()
		self.assertTrue(self.hour_line.x_state == 'approved')
		wizard = invoice_wizard_obj.create({})
		wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_invoices()

		invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
		self.assertEqual(len(invoices),  1)
		invoice = invoices[0]
		self.assertTrue(self.hour_line.x_state == 'customer_invoiced')

		invoice.do_prepare_payment_wsb()

		hour_lines = invoice.x_sale_account_analytic_line_ids
		self.assertNotEqual(len(hour_lines), 0)

		invoice_refund_hour_wizard = invoice_refund_hour_wizard_obj.create({})
		with self.assertRaises(UserError) as e:
			invoice_refund_hour_wizard.do_refund_hour_invoice()
		self.assertIn('invoice', str(e.exception))
		invoice_refund_hour_wizard.invoice_id = invoice

		with self.assertRaises(UserError) as e:
			invoice_refund_hour_wizard.do_refund_hour_invoice()
		self.assertIn("posted moves", str(e.exception))

		invoice.action_post()
		invoice_refund_hour_wizard.do_refund_hour_invoice()

		refund_invoices = account_move_obj.search([('partner_id', '=', self.customer.id),
												   ('move_type', '=', 'out_refund'),
												   ('company_id', '=', self.env.company.id)]
												  )
		self.assertTrue(len(refund_invoices) == 1)
		refund_invoice = refund_invoices[0]
		self.assertEqual(refund_invoice.amount_total, invoice.amount_total)

	def test_standard_hour_book_process(self):
		agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
		commission_payment_line_obj = self.env['oi1_sale_commission_payment_line']
		account_invoice_obj = self.env['account.move']
		account_invoice_line_obj = self.env['account.move.line']
		invoice_wizard_obj = self.env['oi1_werkstandbij.invoice_wizard']
		partner_bank_obj = self.env['res.partner.bank']
		bank_obj = self.env['res.bank']
		account_analytic_line_obj = self.env['account.analytic.line']
		commission_invoice_helper_obj = self.env['oi1_commission_invoice_helper']

		self.assertEqual(self.poule.id, self.sale_order.x_poule_id.id)
		self.free_worker.x_has_vat_on_invoice = False

		self.assertEqual(self.hour_line.x_rate, 15.00)
		self.assertEqual(self.hour_line.unit_amount, 7.0)

		hour_line2 = account_analytic_line_obj.create({
			'x_partner_id': self.free_worker.partner_id.id,
			'x_sale_id': self.sale_order.id,
			'x_from_time': "17:00",
			'x_to_time': "22:00",
			'x_pause_time': "01:00",
			'project_id': self.poule.project_id.id,
			'unit_amount': 4.0,
			'x_rate': 15.00
		})

		self.assertEqual(self.hour_line.x_rate, hour_line2.x_rate)
		self.hour_line.project_id = self.poule.project_id
		self.assertTrue(self.hour_line.x_state == 'concept')

		wizard = agree_hour_line_wizard_obj.create({})


		wizard.with_context({"active_ids": [self.hour_line.id, hour_line2.id]}).do_create_agreements()
		self.assertTrue(self.hour_line.x_state == 'approved')
		wizard = invoice_wizard_obj.create({})
		invoices = wizard.with_context({"active_ids": [self.hour_line.id, hour_line2.id]}).do_create_invoices()
		self.assertNotEqual(len(invoices), 0)
		self.assertTrue(self.hour_line.x_state == 'customer_invoiced')

		customer_invoices = account_invoice_obj.search([('partner_id', '=', self.customer.id)])
		self.assertEqual(len(customer_invoices), 1)
		customer_invoice = customer_invoices[0]
		self.assertEqual(len(customer_invoice.invoice_line_ids), 2)

		surcharge_product_id = self.env.ref('oi1_werkstandbij.invoice_surcharge_product').id
		surcharge_invoice_lines = customer_invoice.invoice_line_ids.filtered(
			lambda l: l.product_id.id == surcharge_product_id)
		worker_customer_invoice_lines = customer_invoice.invoice_line_ids.filtered(
			lambda l: not l.product_id.id == surcharge_product_id)
		self.assertEqual(len(surcharge_invoice_lines), 1)
		self.assertEqual(len(worker_customer_invoice_lines), 1)

		quantity = self.hour_line.unit_amount + hour_line2.unit_amount
		self.assertEqual(worker_customer_invoice_lines.quantity, quantity)

		self.assertEqual(surcharge_invoice_lines.quantity, quantity)
		self.assertEqual(surcharge_invoice_lines.price_subtotal, quantity * 15)

		customer_invoice_lines = account_invoice_line_obj.search([('move_id', '=', customer_invoices[0].id),
																  ('product_id', '=', surcharge_product_id)
																  ])
		self.assertEqual(len(customer_invoice_lines), 1)
		surcharge_invoice_line = customer_invoice_lines[0]
		self.assertEqual(surcharge_invoice_line.price_unit, self.hour_line.project_id.sale_line_id.x_price)
		self.assertEqual(surcharge_invoice_line.price_subtotal,
						  self.hour_line.project_id.sale_line_id.x_price * quantity)
		# Deleting of the invoices will reset the state of the hourlines to approved
		customer_invoice.with_context(check_move_validity=False).unlink()
		self.assertEqual(self.hour_line.x_state , 'approved')
		self.assertEqual(hour_line2.x_state, 'approved')
		self.assertFalse(self.hour_line.x_sale_invoice_id)
		self.assertFalse(hour_line2.x_sale_invoice_id)
		customer_invoices = account_invoice_obj.search([('partner_id', '=', self.customer.id)])
		self.assertEqual(len(customer_invoices), 0)

		# Regenerating of the invoices will work
		wizard.with_context({"active_ids": [self.hour_line.id, hour_line2.id]}).do_create_invoices()
		customer_invoices = account_invoice_obj.search([('partner_id', '=', self.customer.id)])
		self.assertEqual(len(customer_invoices), 1)
		# Invoice can be confirmed
		customer_invoice = customer_invoices[0]
		customer_invoice.action_post()
		self.assertEqual(customer_invoice.state, 'posted')
		# Invoice can be send to WSB
		customer_invoice.do_prepare_payment_wsb()

		rec_count = commission_payment_line_obj.search_count([('account_analytic_line_id', '=', self.hour_line.id)])
		self.assertFalse(rec_count == 0, "There are no commissions created")
		self.assertTrue(self.hour_line.x_sale_invoice_id)
		self.assertTrue(self.hour_line.x_pur_invoice_id)
		self.assertTrue(self.hour_line.x_commission_created)

		# There is one invoice for the freeworker as concept
		free_worker_invoices = account_invoice_obj.search([('partner_id', '=', self.free_worker.partner_id.id)])
		self.assertEqual(len(free_worker_invoices), 1)
		free_worker_invoice = free_worker_invoices[0]
		self.assertEqual(len(free_worker_invoice.invoice_line_ids), 1)

		amount = (self.hour_line.unit_amount * self.hour_line.x_rate)  + (hour_line2.unit_amount * hour_line2.x_rate)
		self.assertEqual(free_worker_invoice.amount_untaxed, amount)
		self.assertEqual(free_worker_invoice.state, 'draft')
		free_worker_invoice.action_post()
		self.assertFalse(not free_worker_invoice.name)
		self.assertEqual(free_worker_invoice.state, 'posted')
		self.assertFalse(self.free_worker.x_has_vat_on_invoice)
		self.assertEqual(free_worker_invoice.amount_tax, 0.0)
		with self.assertRaises(UserError) as e:
			free_worker_invoice.do_prepare_payment_wsb()
		self.assertIn("no email", str(e.exception))

		# Freeworker will get an email
		self.free_worker.email = "test@oi1.nl"
		free_worker_invoice.do_prepare_payment_wsb()

	def test_btw_on_freeworker_invoice_if_has_vat_on_invoice(self):
		agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
		account_invoice_obj = self.env['account.move']

		self.assertFalse(self.hour_line.x_pur_invoice_id.id)
		self.free_worker.x_has_vat_on_invoice = True
		self.free_worker.valid_registration_date = datetime.date.today() + datetime.timedelta(days=7)
		self.assertTrue(self.free_worker.partner_id.x_has_vat_on_invoice)
		self.assertTrue(self.hour_line.project_id.sale_line_id.id)
		wizard = agree_hour_line_wizard_obj.create({})
		invoices = wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_agreements_and_invoice()
		self.assertEqual(len(invoices), 1)
		invoices = invoices[0]
		self.assertNotEqual(len(invoices.x_sale_account_analytic_line_ids), 0)
		self.assertEqual(self.hour_line.x_state,  'customer_invoiced')
		invoices.do_prepare_payment_wsb()

		free_worker_invoices = account_invoice_obj.search([('partner_id', '=', self.free_worker.partner_id.id)])
		self.assertEqual(len(free_worker_invoices), 1)
		free_worker_invoice = free_worker_invoices[0]
		free_worker_invoice.action_post()
		self.assertNotEqual(free_worker_invoice.amount_untaxed, 0.0)
		self.assertEqual(free_worker_invoice.timesheet_count, 0)

		customer_invoice = self.hour_line.x_sale_invoice_id
		self.assertTrue(customer_invoice.id)
		self.assertEqual(customer_invoice.timesheet_count, 1)

		invoice_lines = customer_invoice.invoice_line_ids.filtered(lambda l: len(l.sale_line_ids) > 0)
		self.assertTrue(len(invoice_lines) > 0)
		self.assertNotEqual(free_worker_invoice.amount_tax, 0.0)











