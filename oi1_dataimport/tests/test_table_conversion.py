# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'werkstandbij')
class TestTableConversion(TransactionCase):
	def setUp(self, *args, **kwargs):
		return super().setUp(*args, **kwargs)

	def test_create_table_conversion(self):
		table_conversion_obj = self.env['oi1_dataimport.table_conversion']
		table_conversion = table_conversion_obj.create({})
		self.assertEqual(table_conversion.company_id.id, 1)
