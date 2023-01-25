# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, Form, tagged


@tagged('post_install', 'res.partner')
class TestResPartner(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)
		return result

	def test_create_res_partner(self):
		f = Form(self.env['res.partner'])
		f.x_name = 'test'
		res_partner = f.save()
		self.assertTrue(res_partner.name, 'test')
		self.assertTrue(self.env.user.company_id.partner_id.country_id)
		self.assertEqual(res_partner.country_id.id, self.env.user.company_id.partner_id.country_id.id)
		res_partner.x_firstname = "Klaas"
		self.assertTrue(res_partner.name, 'Klaas test')
		res_partner.x_firstname = ""
		self.assertTrue(res_partner.name, 'test')
		res_partner.x_initials = "J."
		self.assertTrue(res_partner.name, 'J. test')
		res_partner.x_initials = ""
		self.assertTrue(res_partner.name, 'test')


