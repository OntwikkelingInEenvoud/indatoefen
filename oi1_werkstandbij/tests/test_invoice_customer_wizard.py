# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


@tagged('werkstandbij', 'test_invoice_customer_wizard')
class TestPartnerBank(TransactionCase):

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

    def test_invoice_customer_from_2_analytic_hours(self):
        account_analytic_line_obj = self.env['account.analytic.line']
        account_move_obj = self.env['account.move']
        agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
        invoice_wizard_obj = self.env['oi1_werkstandbij.invoice_wizard']

        hour_line_1 = account_analytic_line_obj.create({
            'x_partner_id': self.free_worker.partner_id.id,
            'x_sale_id': self.sale_order.id,
            'x_from_time': "08:00",
            'x_to_time': "17:00",
            'x_pause_time': "21:00",
            'project_id': self.poule.project_id.id,
            'unit_amount': 4.0,
            'x_rate': 15.00
        })

        # An invoice could be created from 2 hourlines
        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [self.hour_line.id, hour_line_1.id]}).do_create_agreements()
        self.assertTrue(self.hour_line.x_state == 'approved')
        wizard = invoice_wizard_obj.create({})
        wizard.with_context({"active_ids": [self.hour_line.id, hour_line_1.id]}).do_create_invoices()
        invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(invoices), 1)
        customer_invoice = invoices[0]
        surcharge_product_id = self.env.ref('oi1_werkstandbij.invoice_surcharge_product').id
        surcharge_invoice_lines = customer_invoice.invoice_line_ids.filtered(
            lambda l: l.product_id.id == surcharge_product_id)
        worker_customer_invoice_lines = customer_invoice.invoice_line_ids.filtered(
            lambda l: not l.product_id.id == surcharge_product_id)
        self.assertEqual(len(surcharge_invoice_lines), 1)
        self.assertEqual(len(worker_customer_invoice_lines), 1)

        quantity = self.hour_line.unit_amount + hour_line_1.unit_amount
        self.assertEqual(worker_customer_invoice_lines.quantity, quantity)

    def test_invoice_customer_from_analytic_hour(self):

        account_analytic_line_obj = self.env['account.analytic.line']
        account_move_obj = self.env['account.move']
        agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
        invoice_wizard_obj = self.env['oi1_werkstandbij.invoice_wizard']

        #An invoice could be created from an hourline
        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_agreements()
        self.assertTrue(self.hour_line.x_state == 'approved')
        wizard = invoice_wizard_obj.create({})
        wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_invoices()
        invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(invoices), 1)

        #Adding a second line should update the invoice
        hour_line_1 = account_analytic_line_obj.create({
            'x_partner_id': self.free_worker.partner_id.id,
            'x_sale_id': self.sale_order.id,
            'x_from_time': "08:00",
            'x_to_time': "17:00",
            'x_pause_time': "02:00",
            'project_id': self.poule.project_id.id,
            'unit_amount': 7.0,
            'x_rate': 15.00
            })

        amount_untaxed = invoices.amount_untaxed
        self.assertNotEqual(amount_untaxed,0)
        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line_1.id]}).do_create_agreements()
        self.assertTrue(hour_line_1.x_state == 'approved')
        wizard = invoice_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line_1.id]}).do_create_invoices()
        invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(invoices), 1)
        self.assertEqual(amount_untaxed*2, invoices.amount_untaxed)

        #Creation of a hourline of a different day should create a different invoice line
        hour_line_2 = account_analytic_line_obj.create({
            'x_partner_id': self.free_worker.partner_id.id,
            'x_sale_id': self.sale_order.id,
            'x_from_time': "08:00",
            'x_to_time': "17:00",
            'x_pause_time': "02:00",
            'project_id': self.poule.project_id.id,
            'unit_amount': 7.0,
            'x_rate': 15.00,
            'date':  datetime.today() - timedelta(days=1)
        })

        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line_2.id]}).do_create_agreements()
        self.assertTrue(hour_line_1.x_state == 'approved')
        wizard = invoice_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line_2.id]}).do_create_invoices()
        invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(invoices), 1)
        self.assertEqual(amount_untaxed * 3, invoices.amount_untaxed)
        self.assertEqual(len(invoices.invoice_line_ids), 3)
        invoices.action_post()

        #After posting a new invoice should be created
        hour_line_3 = account_analytic_line_obj.create({
            'x_partner_id': self.free_worker.partner_id.id,
            'x_sale_id': self.sale_order.id,
            'x_from_time': "08:00",
            'x_to_time': "17:00",
            'x_pause_time': "02:00",
            'project_id': self.poule.project_id.id,
            'unit_amount': 7.0,
            'x_rate': 15.00,
            })

        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line_3.id]}).do_create_agreements()
        self.assertTrue(hour_line_1.x_state == 'approved')
        wizard = invoice_wizard_obj.create({})
        wizard.with_context({"active_ids": [hour_line_3.id]}).do_create_invoices()
        invoices = account_move_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(invoices), 2)