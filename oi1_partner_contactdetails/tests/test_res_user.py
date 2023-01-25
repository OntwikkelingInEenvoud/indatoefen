# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, Form, tagged


@tagged('post_install', 'res.user')
class TestAccountInvoice(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)
		return result

	def test_res_user(self):
		res_user_obj = self.env['res.users']
		name = 'test'
		user = res_user_obj.create({'name': name, 'login':'test'})
		self.assertEqual(user.name, name)
		self.assertEqual(user.x_name, name)
