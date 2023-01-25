# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('oi1')
class TestTest(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)
		user_admin = self.env.ref('base.user_admin')
		self.env = self.env(user=user_admin)
		text_type = self.env.ref('oi1_text.text_type_14')
		text_obj = self.env['oi1_text.text']
		self.text = text_obj.create({'text_type_id': text_type.id, 'name':'tests'})
		return result

	def test_company_id(self):
		self.assertTrue(self.text.company_id, self.env.user.company_id)

	def test_create_slogan(self):
		text_obj = self.env['oi1_text.text']
		text_type = self.env.ref('oi1_text.text_type_16')
		text = False
		text = text_obj.create({'text_type_id': text_type.id, 'name':'tests'})
		self.assertTrue(text.text_type_id.id, text_type.id)
