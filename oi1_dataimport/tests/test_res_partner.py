# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'werkstandbij')
class TestAccountInvoice(TransactionCase):
	def setUp(self, *args, **kwargs):
		return super(TestAccountInvoice, self).setUp(*args, **kwargs)

	def test_create_save_partner_with_x_prev_code(self):
		res_partner_obj = self.env['res.partner']
		res_partner = res_partner_obj.create({'name':'test'})
		self.assertEqual(res_partner.name, 'test')
		res_partner.x_prev_code = False
		res_partner.write({'name': 'test1'})
		self.assertEqual(res_partner.name, 'test1')