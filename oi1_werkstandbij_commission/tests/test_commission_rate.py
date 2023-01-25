# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo import exceptions
import datetime


@tagged('oi1', 'test_commission_rate')
class TestTest(TransactionCase):

    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        self.env.user.lang = False
        return result

    def test_commission_rate(self):
        oi1_commission_rate_obj = self.env['oi1_commission_rate_list']
        oi1_commission_rate_line_obj = self.env['oi1_commission_rate_list_line']
        oi1_commission_rate = oi1_commission_rate_obj.create({'name': 'test_commission_rate'})
        self.assertTrue(oi1_commission_rate.id)

        oi1_commission_rate_line1 = oi1_commission_rate_line_obj.create({'rate_list_id': oi1_commission_rate.id})
        oi1_commission_rate_line1.hour_rate = 15
        oi1_commission_rate_line1.default_rate = 1

        oi1_commission_rate_line2 = oi1_commission_rate_line_obj.create({'rate_list_id': oi1_commission_rate.id})
        oi1_commission_rate_line2.hour_rate = 30
        oi1_commission_rate_line2.default_rate = 2

        current_date = datetime.date.today()
        end_date = current_date - datetime.timedelta(days=360)

        with self.assertRaises(exceptions.UserError) as e:
             oi1_commission_rate_line2.end_date = end_date
        self.assertIn('should be later than a start date', str(e.exception))
        end_date = current_date + datetime.timedelta(days=360)
        oi1_commission_rate_line2.end_date = end_date
        self.assertTrue(oi1_commission_rate_line2.start_date < oi1_commission_rate_line2.end_date)

        tariff = oi1_commission_rate.get_tariff_with_given_hour_rate(10, current_date)
        self.assertEqual(tariff, 0)

        tariff = oi1_commission_rate.get_tariff_with_given_hour_rate(15, current_date)
        self.assertEqual(tariff, 1)

        tariff = oi1_commission_rate.get_tariff_with_given_hour_rate(31, current_date)
        self.assertEqual(tariff, 2)