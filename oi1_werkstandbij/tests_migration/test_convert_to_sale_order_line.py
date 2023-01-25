# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('test_convert_to_sale_order_line')
class TestTest(TransactionCase):

    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        return result

    def test_convert_to_sale_order_line(self):
        convert_wizard = self.env['convert_to_sale_order_line']
        convert_wizard.convert_poule_to_sale_order_line()
        self.assertEqual(1, 2)
