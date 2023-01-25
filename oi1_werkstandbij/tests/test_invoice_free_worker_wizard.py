# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
import datetime


@tagged('test_invoice_free_worker')
class TestInvoiceFreeWorkerWizard(TransactionCase):
    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
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

        self.partner_commission_seller = partner_obj.create({'name': 'commission_seller'})

        commission_product_id = product_obj.create({'name': 'commission product id'})

        commission_seller = commission_obj.create({'name': self.seller_role.name,
                                                   'commission_role_id': self.seller_role.id,
                                                   'product_id': commission_product_id.id,
                                                   'default_rate': 0.10
                                                   })
        commission_partner_obj.create({'partner_id': self.partner_commission_seller.id,
                                       'commission_id': commission_seller.id})

        payment_term = payment_term_obj.search([('company_id', 'in', (self.env.company.id, False))])[0]

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

    def test_create_free_worker_invoices(self):
        account_analytic_line_obj = self.env['account.analytic.line']
        account_move_obj = self.env['account.move']
        agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
        invoice_wizard_obj = self.env['oi1_werkstandbij.invoice_wizard']
        invoice_free_worker_wizard = self.env['oi1_werkstandbij.invoice_free_worker_wizard']

        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_agreements()
        self.assertTrue(self.hour_line.x_state == 'approved')
        wizard = invoice_wizard_obj.create({})
        wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_invoices()
        invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(invoices), 1)
        customer_invoice = invoices[0]

        account_analytic_lines = customer_invoice.invoice_line_ids.x_sales_analytic_account_line_ids
        self.assertFalse(len(account_analytic_lines) == 0)

        invoices =  invoice_free_worker_wizard.create_free_worker_invoices_from_customer_invoices(account_analytic_lines)
        self.assertTrue(len(invoices) == 1)
        free_worker_invoice = invoices[0]
        self.assertEqual(free_worker_invoice.amount_tax, 0.0)
        amount = self.hour_line.unit_amount * self.hour_line.x_rate
        self.assertEqual(free_worker_invoice.amount_untaxed, amount)
        free_worker_invoice.action_post()
        self.assertEqual(free_worker_invoice.state, 'posted')
        free_worker_invoice.button_cancel()
        free_worker_invoice.button_draft()
        self.assertEqual(free_worker_invoice.state, 'draft')

        hour_line = account_analytic_line_obj.create({
            'x_partner_id': self.free_worker.partner_id.id,
            'x_sale_id': self.sale_order.id,
            'x_from_time': "08:00",
            'x_to_time': "17:00",
            'x_pause_time': "02:00",
            'project_id': self.poule.project_id.id,
            'unit_amount': 7.0,
            'x_rate': 15.00
        })

        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line.id]}).do_create_agreements()
        self.assertTrue(hour_line.x_state == 'approved')
        wizard = invoice_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line.id]}).do_create_invoices()
        invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(invoices), 1)
        customer_invoice = invoices[0]
        account_analytic_lines = customer_invoice.invoice_line_ids.x_sales_analytic_account_line_ids
        self.assertTrue(len(account_analytic_lines) == 2)
        invoices = invoice_free_worker_wizard.create_free_worker_invoices_from_customer_invoices(account_analytic_lines)
        self.assertTrue(len(invoices) == 1)
        invoices = account_move_obj.search([('partner_id', '=', self.free_worker.partner_id.id)])
        self.assertEqual(len(invoices), 1)
        free_worker_invoice = invoices[0]
        self.assertEqual(free_worker_invoice.amount_tax, 0.0)
        self.assertEqual(free_worker_invoice.amount_untaxed, 2 * amount)

        hour_line_2 = account_analytic_line_obj.create({
            'x_partner_id': self.free_worker.partner_id.id,
            'x_sale_id': self.sale_order.id,
            'x_from_time': "08:00",
            'x_to_time': "17:00",
            'x_pause_time': "02:00",
            'project_id': self.poule.project_id.id,
            'unit_amount': 8.0,
            'x_rate': 20.00
        })

        # No extra invoice created because the hourline is not invoiced to the customer
        invoices = invoice_free_worker_wizard.create_free_worker_invoices_from_customer_invoices(hour_line_2)
        self.assertFalse(invoices, 0)

        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line_2.id]}).do_create_agreements()
        self.assertTrue(hour_line.x_state == 'approved')
        wizard = invoice_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line_2.id]}).do_create_invoices()
        invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(invoices), 1)
        customer_invoice = invoices[0]
        account_analytic_lines = customer_invoice.invoice_line_ids.x_sales_analytic_account_line_ids
        self.assertTrue(len(account_analytic_lines) == 3)
        invoices = invoice_free_worker_wizard.create_free_worker_invoices_from_customer_invoices(account_analytic_lines)
        self.assertTrue(len(invoices) == 1)
        amount = 2 * amount + (hour_line_2.unit_amount * hour_line_2.x_rate)
        self.assertEqual(free_worker_invoice.amount_tax, 0.0)
        self.assertEqual(free_worker_invoice.amount_untaxed, amount)

    def test_with_vat_on_free_worker_invoice(self):
        account_analytic_line_obj = self.env['account.analytic.line']
        account_move_obj = self.env['account.move']
        agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
        invoice_wizard_obj = self.env['oi1_werkstandbij.invoice_wizard']
        invoice_free_worker_wizard = self.env['oi1_werkstandbij.invoice_free_worker_wizard']


        self.free_worker.x_has_vat_on_invoice = True

        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_agreements()
        self.assertTrue(self.hour_line.x_state == 'approved')
        wizard = invoice_wizard_obj.create({})
        wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_invoices()
        invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(invoices), 1)
        customer_invoice = invoices[0]

        account_analytic_lines = customer_invoice.invoice_line_ids.x_sales_analytic_account_line_ids
        self.assertFalse(len(account_analytic_lines) == 0)
        invoices = invoice_free_worker_wizard.create_free_worker_invoices_from_customer_invoices(account_analytic_lines)
        self.assertTrue(len(invoices) == 1)
        free_worker_invoice = invoices[0]
        self.assertNotEqual(free_worker_invoice.amount_tax, 0.0)
        amount = self.hour_line.unit_amount * self.hour_line.x_rate
        self.assertEqual(free_worker_invoice.amount_untaxed, amount)