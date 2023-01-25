# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('oi1')
class TestSaleOrder(TransactionCase):

    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        self.sale_order = self.env['sale.order'].search([])[0]
        return result

    def test_check_fields(self):
        partner_ids = self.env['res.partner'].search([('is_company', '=', False)], limit=1)
        if len(partner_ids) == 1:
            self.sale_order.partner_id = partner_ids[0]
            self.assertNotEqual(self.sale_order.x_customer_contact, '')
        self.assertNotEqual(len(self.sale_order.x_account_tax_ids), -1)
        has_one_vat = False
        if len(self.sale_order.x_account_tax_ids) == 1:
            has_one_vat = True
        self.assertEqual(self.sale_order.x_has_one_vat, has_one_vat)