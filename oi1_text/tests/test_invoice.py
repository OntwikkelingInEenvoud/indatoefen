# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('-at_install','post_install')
class TestInvoice(TransactionCase):

    def test_check_fields(self):
        self.partner_id = self.env['res.partner'].search([], limit=1)

        self.account_account = self.env['account.account'].create(
            {'user_type_id': self.env.ref('account.data_account_type_revenue').id,
             'code': '80001',
             'company_id': self.env.user.company_id.id,
             'name': 'test_account',
             })

        self.product_template = self.env['product.template'].create({'name': 'test_invoice',
                                                                     'property_account_income_id': self.account_account.id})

        self.assertTrue(self.product_template.property_account_income_id)

        self.journal = self.env['account.journal'].create({
            'name': 'sale_0',
            'code': 'SALE0',
            'type': 'sale',
            'company_id': self.env.user.company_id.id,
            'default_debit_account_id': self.account_account.id,
            'default_credit_account_id': self.account_account.id,
        })

        self.journal_type = self.env['account.journal'].create({
            'name': 'misc_0',
            'code': 'misc_0',
            'type': 'general',
            'company_id': self.env.user.company_id.id
        })

        self.invoice = self.env['account.move'].create(
            {'type': 'out_invoice', 'partner_id': self.partner_id.id, 'journal_id': self.journal.id, })
        self.order = self.env['sale.order'].create({'partner_id': self.partner_id.id})
        self.order_line = self.env['sale.order.line'].create({'order_id': self.order.id,
                                                              'product_id': self.product_template.product_variant_id.id,
                                                              'product_uom_qty': 999,
                                                              'price_unit': 0.1, })
        self.order.action_confirm()
        self.order._create_invoices()
        self.invoice_order = False
        invoice_orders = self.env['account.move.line'].search([('sale_line_ids', '!=', False)], limit=1)
        if len(invoice_orders) > 0:
            self.invoice_order = invoice_orders[0].move_id
        self.concept_invoice = False
        concept_invoices = self.env['account.move'].search([('state', '=', 'draft'), ('partner_id', '!=', False)],
                                                           limit=1)
        if len(concept_invoices) > 0:
            self.concept_invoice = concept_invoices[0]

        user_admin = self.env.ref('base.user_admin')
        self.env = self.env(user=user_admin)
        text_obj = self.env['oi1_text.text']
        text_type = self.env.ref('oi1_text.text_type_14')
        texts = text_obj.search([('text_type_id', '=', text_type.id)])
        if len(texts) == 0:
            text_obj.create({'text_type_id': text_type.id, 'name': 'tests'})
        text_type = self.env.ref('oi1_text.text_type_15')
        texts = text_obj.search([('text_type_id', '=', text_type.id)])
        if len(texts) == 0:
            text_obj.create({'text_type_id': text_type.id, 'name': 'tests'})
        text_type = self.env.ref('oi1_text.text_type_11')
        texts = text_obj.search([('text_type_id', '=', text_type.id)])
        if len(texts) == 0:
            text_obj.create({'text_type_id': text_type.id, 'name': 'tests'})
        # Company slogan
        text_type = self.env.ref('oi1_text.text_type_16')
        texts = text_obj.search([('text_type_id', '=', text_type.id)])
        if len(texts) == 0:
            text_obj.create({'text_type_id': text_type.id, 'name': 'tests'})


        if self.invoice_order:
            self.assertGreater(len(self.invoice_order.get_related_sale_orders()), 0)
            self.assertNotEqual(self.invoice_order.order_user_names, '')
        self.assertNotEqual(self.invoice.report_header_text_not_html, False)
        self.assertNotEqual(self.invoice.report_footer_text_not_html, False)
        self.assertNotEqual(self.invoice.report_delivery_terms, False)
        self.assertNotEqual(self.invoice.company_slogan_not_html, False)


        # Testing the orderreference
        for order in self.invoice.get_related_sale_orders():
            order.client_order_ref = ''
            self.assertEqual(self.invoice.order_reference, '')
        for order in self.invoice.get_related_sale_orders():
            order.client_order_ref = 'tests'
            self.assertNotEqual(self.invoice.order_reference, '')

        # Testing the vat display
        if self.concept_invoice:
            self.concept_invoice.partner_id.parent_id = False
            self.assertFalse(self.concept_invoice.partner_id.parent_id)
            self.concept_invoice.partner_id.vat = 'NL123456782B90'
            self.assertTrue(self.concept_invoice.partner_id.vat)
            self.assertEqual(self.concept_invoice.is_vat_visible, True)
            self.concept_invoice.partner_id.vat = ''
            self.concept_invoice.fiscal_position_id = False
            with self.assertRaises(ValueError) as e:
                fiscal_position = self.env.ref('l10n_nl.fiscal_position_template_national')
                self.assertEqual(self.concept_invoice.is_vat_visible, False)
            self.assertIn('l10n_nl.fiscal_position_template_national', str(e.exception))


        if len(self.invoice.get_related_sale_orders()) > 0:
            partner_ids = self.env['res.partner'].search([('is_company', '=', False)], limit=1)
            if len(partner_ids) == 1:
                self.invoice_order.order_ids[0].partner_id = partner_ids[0]
                self.assertNotEqual(self.invoice.order_customer_contact, '')

        is_one_order = False
        if len(self.invoice.get_related_sale_orders()) == 1:
            is_one_order = True
        self.assertEqual(self.invoice.x_is_one_order, is_one_order)

        if self.invoice_order:
            if len(self.invoice_order.get_related_sale_orders()) > 0:
                self.assertNotEqual(self.invoice_order.order_names, '')
            else:
                self.assertEqual(self.invoice_order.order_names, '')
