# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
from odoo import Command, exceptions, _
import datetime


@tagged('post_install', 'test_account_invoice','-at_install')
class TestAccountInvoice(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)


		account_analytic_line_obj = self.env['account.analytic.line']
		payment_term_obj = self.env['account.payment.term']
		poule_obj = self.env['oi1_freeworkerpoule']
		res_partner_obj = self.env['res.partner']
		sale_obj = self.env['sale.order']
		product_obj = self.env['product.template']

		self.env.user.lang = False
		self.customer = res_partner_obj.create({'name': 'test_customer'})

		aa_lines = account_analytic_line_obj.search([('x_sale_invoice_id', '!=', False)], limit=1)
		self.account_invoice_all_sales = False
		if len(aa_lines) == 1:
			self.account_invoice_all_sales = aa_lines[0].x_sale_invoice_id
		aa_lines = account_analytic_line_obj.search([('x_pur_invoice_id', '!=', False)], limit=1)
		self.account_invoice_all_purchase = False
		if len(aa_lines) == 1:
			self.account_invoice_all_purchase = aa_lines[0].x_pur_invoice_id
			self.account_invoice_all_purchase.invoice_date = datetime.datetime.today()

		self.account_invoice_with_no_work_hour = False
		invoice_lines = self.env['account.move.line'].search([], limit=250)
		for invoice_line in invoice_lines:
			aa_lines = account_analytic_line_obj.search([('x_pur_invoice_line_id', '=', invoice_line.id)], limit=1)
			if len(aa_lines) == 0:
				self.account_invoice_with_no_work_hour = invoice_line.move_id
				break
		self.partner_id = res_partner_obj.create({'name': 'test partner bank account', 'email': 'testpartnerbankaccount@oi1.nl'})
		self.beneficiary = res_partner_obj.create({'name': 'test beneficiary'})

		self.product = product_obj.create({'name': 'test_product', 'type': 'service'})
		self.poule = poule_obj.create({'name': 'test poule',
									   'act_description': 'test activiteit',
									   'product_id': self.product.product_variant_id.id})

		payment_term = payment_term_obj.search([('company_id', 'in', (self.env.company.id, False))])[0]
		self.sale_order = sale_obj.create({'partner_id': self.customer.id,
										   'payment_term_id': payment_term.id})

		self.hour_line = account_analytic_line_obj.create({
			'x_partner_id': self.env['res.partner'].create({'name': 'test freeworker'}).id,
			'x_from_time': "17:00",
			'x_to_time': "22:00",
			'x_pause_time': "01:00",
			'unit_amount': 4.0,
			'x_rate': 15.00,
			'x_sale_id': self.sale_order.id,
			'project_id': self.poule.project_id.id,
		})
		return result


	def test_send_free_worker_specification(self):
		account_analytic_line_obj = self.env['account.analytic.line']
		res_partner_bank_obj = self.env['res.partner.bank']
		res_bank_obj = self.env['res.bank']
		account_analytic_line = account_analytic_line_obj.search([('x_pur_invoice_line_id', '!=', False)], limit=1)
		if len(account_analytic_line) == 1:
			invoice = account_analytic_line.x_pur_invoice_id
			free_worker = invoice.partner_id
			self.assertTrue(free_worker.id)
			bank_id = res_bank_obj.create({'name': 'test_bank'})
			self.assertTrue(bank_id.id)
			res_partner_bank = res_partner_bank_obj.create({'partner_id': free_worker.id,
															'bank_id': bank_id.id,
															'acc_number': 'BE71096123456769'
															})
			self.assertTrue(res_partner_bank.id)
			self.assertTrue(invoice.id)
			invoice.partner_bank_id = res_partner_bank
			self.assertTrue(invoice.partner_bank_id.id)
			invoice.partner_bank_id.bank_id = self.env['res.bank'].search([], limit=1)
			self.assertTrue(invoice.partner_bank_id.bank_id.id)
			partner_id = invoice.partner_id
			self.assertTrue(partner_id.x_freeworker_id.id)
			freeworker = partner_id.x_freeworker_id
			self.assertTrue(freeworker.id)
			freeworker.x_has_vat_on_invoice = False
			self.assertTrue(len(invoice.get_attachments_ids_mail_freeworker_specification(invoice)) == 1)
			freeworker.x_has_vat_on_invoice = True
			self.assertTrue(len(invoice.get_attachments_ids_mail_freeworker_specification(invoice)) == 2)
			freeworker.email = False
			with self.assertRaises(UserError) as e:
				self.assertTrue(invoice.do_email_freeworker_specification())
			self.assertIn('no email', str(e.exception))
			free_worker.email = "test@oi1.nl"
			self.assertTrue(invoice.do_email_freeworker_specification())


	def test_invoice_buttons_visible_manually_created_invoice(self):
		account_invoice_obj = self.env['account.move']
		account_invoice_line_obj = self.env['account.move.line']
		account_invoice = account_invoice_obj.create({'partner_id': self.partner_id.id,
													  'move_type': 'out_invoice',
													  'partner_bank_id': self.env.company.x_default_sales_bankId.id,
													  })

		product_template = self.env['product.template'].search([], limit=1)
		self.assertTrue(len(product_template) == 1)
		account_invoice_line = self.create_account_invoice_move_line_from_product\
			(account_invoice, product_template.product_variant_id, 60, 1)
		self.assertEqual(account_invoice_line.display_type, 'product')
		self.assertTrue(not account_invoice.x_is_invoice_refund_visible)
		self.assertTrue(not account_invoice.x_is_print_partner_specification_visible)
		self.assertTrue(not account_invoice.x_is_booked_hour_invoice)
		account_invoice.action_post()
		self.assertNotEqual(len(account_invoice.line_ids), 0)
		self.assertTrue(account_invoice.x_is_invoice_refund_visible)
		self.assertTrue(not account_invoice.x_is_print_partner_specification_visible)
		self.assertTrue(not account_invoice.x_is_booked_hour_invoice)

	def test_invoice_buttons_visible_hour_created_invoice(self):
		account_analytic_line = self.hour_line
		account_invoice_obj = self.env['account.move']
		account_invoice_line_obj = self.env['account.move.line']
		partner_bank_obj = self.env['res.partner.bank']
		bank_obj = self.env['res.bank']

		bank = bank_obj.create({'name': 'test bank', 'bic': 'test01'})
		acc_number = 'NL70TRIO0123456789'
		partner_bank_ids = partner_bank_obj.search([('acc_number','=', acc_number)])
		partner_bank_ids.unlink()
		partner_bank_id = partner_bank_obj.create({'acc_number': acc_number,
												   'partner_id': self.partner_id.id,
												   'bank_id': bank.id
												   })

		product_template = self.env['product.template'].search([], limit=1)
		account_id = self.env['account.account'].search([('company_id', '=', self.env.company.id)], limit=1)
		self.assertTrue(len(product_template) == 1)
		self.assertEqual(len(account_id), 1)

		account_invoice = self.create_test_invoice()

		account_invoice.partner_bank_id = partner_bank_id
		#2021_0709 Simulate that the hourline is already processed 
		account_analytic_line.write({'x_state': 'invoiced'})
		with self.assertRaises(UserError) as e:
			account_analytic_line.write({'x_pur_invoice_line_id': account_analytic_line.id})
		self.assertIn('Only hourlines in the state concept can be changed', str(e.exception))
		account_analytic_line.write({'system':1,
									 'x_sale_invoice_line_id': account_invoice.invoice_line_ids[0].id,
									 'timesheet_invoice_id': False})

		self.assertTrue(account_invoice.x_pur_invoice_analytic_line_count == 0)
		self.assertTrue(account_invoice.x_sale_invoice_analytic_line_count > 0)
		self.assertTrue(not account_invoice.x_is_invoice_refund_visible)
		self.assertTrue(not account_invoice.x_is_print_partner_specification_visible)
		self.assertTrue(account_invoice.x_is_booked_hour_invoice)
		self.assertTrue(account_invoice.partner_bank_id.id)
		account_invoice.action_post()
		self.assertTrue(account_invoice.x_is_invoice_refund_visible)
		self.assertTrue(not account_invoice.x_is_print_partner_specification_visible)
		self.assertTrue(account_invoice.x_is_booked_hour_invoice)
		account_invoice.action_invoice_sent()

		account_invoice = account_invoice_obj.create({'partner_id': self.partner_id.id,
													  'move_type': 'in_invoice',
													  'partner_bank_id': self.env.company.x_default_sales_bankId.id,
													  'invoice_date': datetime.date.today(),
													  })

		account_invoice_line = self.create_account_invoice_move_line_from_product \
			(account_invoice, product_template.product_variant_id, 125, 2)

		account_analytic_line.write({'system': 1, 'x_pur_invoice_line_id': account_invoice_line.id})
		self.assertTrue(account_analytic_line.x_pur_invoice_id.id)
		account_invoice = account_invoice_obj.browse([account_invoice.id])
		self.assertTrue(account_invoice.x_pur_invoice_analytic_line_count > 0)
		self.assertTrue(account_invoice.x_sale_invoice_analytic_line_count == 0)
		self.assertTrue(not account_invoice.x_is_invoice_refund_visible)
		self.assertTrue(not account_invoice.x_is_print_partner_specification_visible)
		self.assertTrue(account_invoice.x_is_booked_hour_invoice)
		account_invoice.action_post()
		self.assertTrue(account_invoice.x_is_invoice_refund_visible)
		self.assertTrue(account_invoice.x_is_print_partner_specification_visible)
		self.assertTrue(account_invoice.x_is_booked_hour_invoice)
		self.partner_id.email = 'test@oi1.nl'
		account_invoice.partner_bank_id.bank_id = self.env['res.bank'].search([], limit=1)

	def test_manually_created_invoice(self):
		account_invoice_obj = self.env['account.move']
		account_invoice_line_obj = self.env['account.move.line']
		account_invoice = account_invoice_obj.create({'partner_id': self.partner_id.id,
													  'move_type': 'out_invoice',
													  'partner_bank_id': self.env.company.x_default_sales_bankId.id})

		product_template = self.env['product.template'].search([], limit=1)

		self.assertTrue(len(product_template) == 1)
		account_move_line = account_invoice_line_obj.with_context(check_move_validity=False).create({'move_id': account_invoice.id,
										 'name': 'test_manually_created_invoice',
										 'product_id': product_template.product_variant_id.id,
										 'quantity': 60,
										 'price_unit': 1,
										 'account_id': account_invoice.journal_id.default_account_id.id,
										 'display_type': 'product',
										 })
		self.assertTrue(account_move_line.id)
		self.assertTrue(account_move_line.display_type == 'product')
		self.assertNotEqual(len(account_invoice.line_ids), 0)
		account_invoice.action_post()
		account_invoice = account_invoice_obj.browse([account_invoice.id])
		self.assertNotEqual(len(account_invoice.line_ids), 0)
		self.assertTrue(account_invoice.name != '')
		self.assertTrue(not account_invoice.invoice_origin)


	def test_booked_hours_sale_invoice(self):
		if self.account_invoice_all_sales:
			self.assertNotEqual(self.account_invoice_all_sales.x_sale_invoice_analytic_line_count, 0)
			self.assertEqual(self.account_invoice_all_sales.x_partner_year_amount, 0)
			self.assertEqual(len(self.account_invoice_all_sales.x_account_analytic_line_ids), 0)
			self.assertNotEqual(self.account_invoice_all_sales.x_poule_ids, 0)
			self.account_invoice_all_sales.do_prepare_payment_wsb()
			account_analytic_lines = self.account_invoice_all_sales.x_sale_account_analytic_line_ids
			free_worker_invoices = account_analytic_lines.x_pur_invoice_id
			self.assertTrue(len(free_worker_invoices) > 0)
			free_worker_invoice = free_worker_invoices[0]
			self.assertEqual(free_worker_invoice.x_sale_invoice_analytic_line_count, 0)
			self.assertNotEqual(free_worker_invoice.x_partner_year_amount, 0)
			self.assertNotEqual(len(free_worker_invoice.x_account_analytic_line_ids), 0)
			self.assertNotEqual(free_worker_invoice.x_poule_ids, 0)

	def test_booked_hours_pur_invoice(self):
		if self.account_invoice_all_purchase:
			self.assertNotEqual(len(self.account_invoice_all_purchase.x_account_analytic_line_ids), 0)
			self.assertNotEqual(self.account_invoice_all_purchase.x_partner_year_amount, 0)

	def test_invoice_without_not_booked(self):
		if self.account_invoice_with_no_work_hour:
			self.assertNotEqual(len(self.account_invoice_with_no_work_hour.x_no_work_invoice_line_ids), 0,
								str(self.account_invoice_with_no_work_hour.name) + " has no workhours calculated")

	def create_test_invoice(self):
		journal_obj = self.env['account.journal']
		account_move_line_obj = self.env['account.move.line']

		purchase_journal_id = journal_obj.search([('type', '=', 'purchase'), ('company_id','=', self.env.company.id)], limit=1)
		self.assertEqual(len(purchase_journal_id), 1)

		tax = self.env['account.tax'].search(
			[('type_tax_use', '=', 'purchase'), ('company_id', '=', self.env.company.id)], limit=1)
		product_ids = self.env['product.product'].search([], limit=1)
		if len(product_ids) > 0:
			product_id = product_ids[0]

		invoice_line_account = self.env['account.account'].search(
			[('account_type', '=', 'expense'),
			 ('company_id', '=', self.env.company.id)], limit=1)

		invoice = self.env['account.move'].create({'partner_id': self.partner_id.id,
													  'move_type': 'in_invoice',
												   	  'journal_id' : purchase_journal_id.id,
												   	  'company_id' : self.env.company.id,
												   	  'invoice_date' : datetime.date.today(),
													  })
		self.assertEqual(invoice.journal_id.type, 'purchase')

		move_line = account_move_line_obj.create({
												 'product_id': product_id.id,
												 'quantity': 1.0,
												 'price_unit': 100.0,
												 'move_id': invoice.id,
												 'name': 'product that cost 100',
												 'account_id': invoice_line_account.id,
												 'company_id': self.env.company.id,
												 'tax_ids': [(6, 0, [tax.id])],
												 'display_type': 'product',
												 })
		self.assertTrue(move_line.id != 0)
		self.assertGreater(len(invoice.invoice_line_ids), 0)
		return invoice

	def test_x_partner_year_amount(self):
		account_invoice_obj = self.env['account.move']
		invoice = account_invoice_obj.search([('move_type', '=', 'in_invoice')], limit=1)
		start_date = datetime.datetime(datetime.datetime.now().year, 1, 1)
		end_date = datetime.datetime(datetime.datetime.now().year, 12, 31)
		if invoice.invoice_date:
			start_date = datetime.datetime(invoice.invoice_date.year, 1, 1)
			end_date = datetime.datetime(invoice.invoice_date.year, 12, 31)
		invoices = account_invoice_obj.search([('partner_id', '=', invoice.partner_id.id),
											   ('move_type','in',('in_invoice','in_refund')),
											   ('invoice_date', '>', start_date),
											   ('invoice_date', '<', end_date),
											   ])
		amount = 0.0
		for invoice_check in invoices.filtered(lambda l: l.state == 'posted'):
			amount += round (invoice_check.amount_total, 2)
		self.assertEqual(round(amount, 2), round(invoice.x_partner_year_amount, 2))

	def test_is_freeworker_visible(self):
		account_analytic_line_obj = self.env['account.analytic.line']
		account_analytic_line = account_analytic_line_obj.search([('x_pur_invoice_line_id', '!=', False)], limit=1)

		if len(account_analytic_line) > 0:
			invoice = account_analytic_line.x_pur_invoice_id
			self.assertTrue(invoice.x_is_freeworker_visible)
			self.assertFalse(not invoice.x_freeworker_id.id)

	def create_account_invoice_move_line_from_product(self, move_id, product_id, quantity=False, price_unit=False,
													  name=False):
		account_id = False
		taxes = False
		if not name:
			name = product_id.name
		if not price_unit:
			price_unit = product_id.list_price
		if not quantity:
			quantity = 1
		if move_id.move_type in ('out_invoice', 'out_refund'):
			account_id, taxes = self.get_sales_invoice_line_data(product_id, move_id)
		if move_id.move_type in ('in_invoice', 'in_refund'):
			account_id, taxes = self.get_purchase_invoice_line_data(product_id, move_id)
		values = {'quantity': quantity,
				  'price_unit': price_unit,
				  'name': name,
				  'product_id': product_id.id,
				  'account_id': account_id.id,
				  'tax_ids': [(6, 0, taxes)],
				  'display_type': 'product'
				  }
		move_id.write({'line_ids': [Command.create(values)]})
		return move_id.line_ids.filtered(lambda l: l.display_type == 'product').sorted(key=lambda r: -r.id)[0]

	def get_sales_invoice_line_data(self, product_id, move_id):
		account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
		if not account_id:
			account_id = move_id.journal_id.default_account_id
		if not account_id.id:
			raise exceptions.UserError(
				_("Please provide an income account for product %s") % product_id.product_tmpl_id.name)
		taxes = self.add_sales_taxes(product_id, move_id)
		return account_id, taxes

	def add_sales_taxes(self, product_id, move_id):
		taxes = product_id.taxes_id.filtered(lambda l: l.company_id.id == self.env.company.id)
		fiscal_position_id = move_id.partner_id.property_account_position_id
		if fiscal_position_id and taxes:
			tax_ids = fiscal_position_id.map_tax(taxes, product_id, move_id.partner_id).ids
		else:
			tax_ids = taxes.ids
		return tax_ids

	def get_purchase_invoice_line_data(self, product_id, move_id):
		account_id = product_id.property_account_expense_id or product_id.categ_id.property_account_expense_categ_id
		if not account_id:
			account_id = move_id.journal_id.default_account_id
		if not account_id.id:
			raise exceptions.UserError(
				_("Please provide an income account for product %s") % product_id.product_tmpl_id.name)
		taxes = self.get_taxes_purchase_product_id(product_id, move_id)
		return account_id, taxes

	def get_taxes_purchase_product_id(self, product_id, partner_id, fiscal_position_id=False, company_id=False):
		if not company_id:
			company_id = self.env.company
		taxes = product_id.supplier_taxes_id.filtered(
			lambda r: r.company_id.id == company_id.id)
		if fiscal_position_id and taxes:
			tax_ids = fiscal_position_id.map_tax(taxes, product_id, partner_id).ids
		else:
			tax_ids = taxes.ids
		return tax_ids





