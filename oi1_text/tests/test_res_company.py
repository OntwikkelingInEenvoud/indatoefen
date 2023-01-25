# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('oi1')
class TestTest(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)

		self.company = self.env.user.company_id
		text_obj = self.env['oi1_text.text']
		text_type = self.env.ref('oi1_text.text_type_16')
		texts = text_obj.search([('text_type_id', '=', text_type.id)])
		if len(texts) == 0:
			text_obj.create({'text_type_id': text_type.id, 'name': 'tests'})
		return result

	def test_company_slogan(self):
		self.assertFalse(self.company.x_company_slogan_not_html, False)

	def test_delivery_partner_id(self):
		self.assertNotEqual(self.company.x_delivery_partner_id.id, False)