from odoo.tests.common import TransactionCase, tagged
import datetime


@tagged('test_commission_invoice_payments_by_a_freeworker')
class TestCommissionPayedByFreeWorker(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)
		test_company_id = 1

		self.x_price = 15
		self.c_commission_rate = 0.1
		self.c_unit_amount = 5.0
		self.c_rate = 17.50

		account_analytic_line_obj = self.env['account.analytic.line']
		commission_obj = self.env['oi1_commission']
		payment_term_obj = self.env['account.payment.term']
		product_obj = self.env['product.product']
		res_partner_obj = self.env['res.partner']
		commission_partner_obj = self.env['oi1_commission_partner']
		free_worker_obj = self.env['oi1_free_worker']
		sale_order_obj = self.env['sale.order']
		sale_order_line_obj = self.env['sale.order.line']

		self.commission_product_id = product_obj.create({'name': 'test commission product'})
		self.flex_assistant_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_practical_work_planner')
		self.free_worker_commission = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_free_worker_commission')

		self.flex_commission = commission_obj.create({'commission_role_id': self.flex_assistant_role.id,
													  'name': 'test commission payment by freeworker',
													  'product_id': self.commission_product_id.id,
													  'payment_by': 'freeworker',
													  'default_rate': self.c_commission_rate
													  })

		self.flex_commission_partner = res_partner_obj.create({'name': 'flex commission partner'})

		self.commission_partner = commission_partner_obj.create({'partner_id': self.flex_commission_partner.id,
																 'commission_role_id': self.flex_assistant_role.id,
																 'commission_id': self.flex_commission.id,
																 })
		self.free_worker = free_worker_obj.create({'name': 'test_free_worker'})
		self.free_worker.practical_work_planner_partner_id = self.flex_commission_partner

		self.customer_partner = res_partner_obj.create({'name': 'test_customer'})
		self.company_id = self.env['res.company'].browse([test_company_id])

		payment_term = payment_term_obj.search([('company_id', 'in', (self.company_id.id, False))])[0]

		self.sale_order = sale_order_obj.create({'partner_id': self.customer_partner.id,
												 'payment_term_id': payment_term.id,
												 })

		self.product = self.env.ref('oi1_werkstandbij.product_template_free_workers_poule')

		self.sale_order_line = sale_order_line_obj.create({'order_id': self.sale_order.id,
														   'product_id': self.product.id,
														   'x_price': self.x_price,
														   })
		self.sale_order.action_confirm()

		self.hour_line = account_analytic_line_obj.create({
			'x_partner_id': self.free_worker.partner_id.id,
			'x_sale_id': self.sale_order.id,
			'x_from_time': "08:00",
			'x_to_time': "15:00",
			'x_pause_time': "02:00",
			'project_id': self.sale_order.x_poule_ids[0].project_id.id,
			'unit_amount': self.c_unit_amount,
			'x_rate': self.c_rate,
		})

		return result

	def test_creation_and_payment_of_the_commission_which_is_payed_by_a_freeworker(self):
		account_invoice_obj = self.env['account.move']
		agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
		sale_commission_payment_obj = self.env['oi1_sale_commission_payment']
		self.assertEqual(len(self.sale_order.x_poule_ids), 1)
		self.assertTrue(self.hour_line.id)
		wizard = agree_hour_line_wizard_obj.create({})
		wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_agreements_and_invoice()
		invoices = account_invoice_obj.search([('partner_id', '=', self.customer_partner.id)])
		self.assertEqual(len(invoices), 1)
		self.assertEqual(invoices.amount_untaxed, self.c_unit_amount * (self.c_rate + self.x_price),
						  "Wrong calculation of the customer invoice")
		self.assertNotEqual(self.hour_line.x_state, 'invoiced')
		invoices.do_prepare_payment_wsb()
		self.assertEqual(self.hour_line.x_state, 'customer_invoiced')

		free_worker_invoices = account_invoice_obj.search([('partner_id', '=', self.free_worker.partner_id.id)])
		self.assertEqual(len(free_worker_invoices),1)
		self.assertEqual(free_worker_invoices.amount_untaxed, (self.c_rate - self.c_commission_rate) * self.c_unit_amount)

		sale_commission_payments = sale_commission_payment_obj.search([('partner_id', '=', self.flex_commission_partner.id)])
		self.assertEqual(len(sale_commission_payments), 1)
		self.assertEqual(sale_commission_payments.amount, self.c_commission_rate * self.c_unit_amount)



	def test_payment_of_freeworker_commission(self):
		self.free_worker.practical_work_planner_partner_id = False
		account_invoice_obj = self.env['account.move']
		agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
		commission_obj = self.env['oi1_commission']
		commission_free_worker_obj = self.env['oi1_commission_free_worker']
		sale_commission_payment_obj = self.env['oi1_sale_commission_payment']

		commission_for_free_worker = commission_obj.create({'commission_role_id': self.free_worker_commission.id,
													  'name': 'test commission payment for freeworker',
													  'product_id': self.commission_product_id.id,
													  'payment_by': 'freeworker',
													  'default_rate': self.c_commission_rate * 2,
													  'commission_beneficiary_partner_id' : self.flex_commission_partner.id,
													  })


		commission_free_worker = commission_free_worker_obj.create({'free_worker_id': self.free_worker.id,
		 								   'commission_id': commission_for_free_worker.id})
		self.assertTrue(commission_free_worker.id)


		self.assertTrue(commission_for_free_worker.id)

		wizard = agree_hour_line_wizard_obj.create({})
		wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_agreements_and_invoice()
		invoices = account_invoice_obj.search([('partner_id', '=', self.customer_partner.id)])
		self.assertEqual(len(invoices), 1)
		self.assertEqual(invoices.amount_untaxed, self.c_unit_amount * (self.c_rate + self.x_price),
						  "Wrong calculation of the customer invoice")
		self.assertNotEqual(self.hour_line.x_state, 'invoiced')
		invoices.do_prepare_payment_wsb()
		self.assertEqual(self.hour_line.x_state, 'customer_invoiced')

		free_worker_invoices = account_invoice_obj.search([('partner_id', '=', self.free_worker.partner_id.id)])
		self.assertEqual(len(free_worker_invoices), 1)
		self.assertEqual(free_worker_invoices.amount_untaxed,
						  (self.c_rate - self.c_commission_rate * 2) * self.c_unit_amount)

		sale_commission_payments = sale_commission_payment_obj.search(
			[('partner_id', '=', self.flex_commission_partner.id)])
		self.assertEqual(len(sale_commission_payments), 1)
		self.assertEqual(sale_commission_payments.amount, self.c_commission_rate * self.c_unit_amount * 2)
