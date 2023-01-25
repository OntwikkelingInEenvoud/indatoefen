# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
import datetime

@tagged('post_install', 'test_res_partner', '-at_install')
class TestAccountInvoice(TransactionCase):
	def setUp(self, *args, **kwargs):
		result = super(TestAccountInvoice, self).setUp(*args, **kwargs)
		self.env.user.lang = False

		# Add the user to the freeworker for access rights
		freeworker_group = self.env.ref('oi1_free_worker.freeworker_view_group')
		freeworker_group.write({'users': [(4, self.env.user.id)]})
		return result


	def test_res_partner_period(self):
		res_partner_obj = self.env['res.partner']
		partner = res_partner_obj.create({'name': 'respartner'})
		date = datetime.datetime(2020, 9, 7)
		period = partner.get_commission_period(partner, date)
		self.assertTrue("202037" in period)
		partner.x_commission_period = 'mm'
		period = partner.get_commission_period(partner, date)
		self.assertTrue("202009" in period)
		partner.x_commission_period = 'yy'
		period = partner.get_commission_period(partner, date)
		self.assertTrue("2020" in period)
		partner.x_commission_period = 'manual'
		period = partner.get_commission_period(partner, date)
		self.assertTrue('Manual' in period, period)

