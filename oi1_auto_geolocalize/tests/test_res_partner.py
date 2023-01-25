# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'account.invoice')
class TestResPartner(TransactionCase):

    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        return result

    def test_cron_geo_localize(self):
        res_partner_obj = self.env['res.partner']
        res_partner_obj.cron_geo_localize()
