# -*- coding: utf-8 -*-
from odoo import exceptions
from odoo.tests.common import TransactionCase, tagged
import datetime


@tagged('oi1', 'test_oi1_commission_log')
class TestTest(TransactionCase):

    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        partner_obj = self.env['res.partner']
        commission_obj = self.env['oi1_commission']
        product_obj = self.env['product.product']
        commission_main_obj = self.env['oi1_commission_main']

        self.env.user.lang = False

        self.commission_product = product_obj.create({'name': 'test_commission_product'})

        self.practical_commission = commission_obj.create({'name': 'test_practical_work_planner_commission',
                                                           'commission_role_id': self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_practical_work_planner').id,
                                                           'product_id': self.commission_product.id
                                                           })
        self.recruiter_commission = commission_obj.create({'name': 'test_recruiter',
                                                           'commission_role_id': self.env.ref(
                                                               'oi1_commission_role_recruiter').id,
                                                           'product_id': self.commission_product.id
                                                           })

        self.practical_work_planner_partner_id = partner_obj.create({'name': 'test_practical_work_planner'})
        self.recruiter_commission_partner_id = partner_obj.create({'name': 'test_recruiter'})

        commission_main_obj.create({'partner_id': self.practical_work_planner_partner_id.id, 'commission_id': self.practical_commission.id})
        commission_main_obj.create(
            {'partner_id': self.recruiter_commission_partner_id.id, 'commission_id': self.recruiter_commission.id})

        return result

    def test_start_date_on_first_log(self):
        free_worker_obj = self.env['oi1_free_worker']
        partner_obj = self.env['res.partner']

        free_worker = free_worker_obj.create({'name': 'test'})
        self.assertTrue(free_worker.id)
        
        practical_work_planner_partner_id = self.practical_work_planner_partner_id
        free_worker.write({'practical_work_planner_partner_id' : practical_work_planner_partner_id})

        commission_logs = free_worker.commission_log_ids
        self.assertEqual(len(commission_logs), 1)
        commission_log = commission_logs[0]
        self.assertTrue(commission_log.start_date < datetime.date.today() - datetime.timedelta(days=10))

        recruiter_partner_ids = partner_obj.search([('x_is_recruiter', '=', True)])
        self.assertFalse(len(recruiter_partner_ids) == 0)
        recruiter_partner_id = recruiter_partner_ids[0]
        free_worker.write({'recruiter_partner_id': recruiter_partner_id})
        commission_logs = free_worker.commission_log_ids
        self.assertEqual(len(commission_logs), 2)

        for commission_log in commission_logs:
            self.assertTrue(commission_log.start_date < datetime.date.today() - datetime.timedelta(days=10))

        self.assertFalse(len(recruiter_partner_ids) == 2)
        recruiter_partner_id = recruiter_partner_ids[1]
        free_worker.write({'recruiter_partner_id': recruiter_partner_id})
        commission_logs = free_worker.commission_log_ids.\
            filtered(lambda l: l.start_date > datetime.date.today() - datetime.timedelta(days=5))
        self.assertTrue(len(commission_logs) == 1)

    def test_constrains_end_date_start_date(self):
        commission_log_obj = self.env['oi1_commission_log']
        commission_role_obj = self.env['oi1_commission_role']

        partner_obj = self.env['res.partner']
        sale_order_obj = self.env['sale.order']

        partner_1 = partner_obj.create({'name': "test_partner1"})
        sale_order = sale_order_obj.create({'partner_id': partner_1.id})
        com_partner_1 = partner_obj.create({'name': 'test_commission_partner1'})
        model_name = 'sale.order'
        start_date = datetime.date.today()
        commission_log = commission_log_obj.set_commission_log(model_name,
                                                               sale_order.id,
                                                               com_partner_1,
                                                               commission_role_obj.get_seller_role(),
                                                               start_date,
                                                               False,
                                                               4.0)
        self.assertTrue(commission_log.id)

        commission_log.end_date = start_date

        commission_log.write({'end_date': datetime.date.today() - datetime.timedelta(days=1)})

        with self.assertRaises(exceptions.UserError) as e:
            commission_log.end_date = datetime.date.today() - datetime.timedelta(days=1)
            commission_log.start_date = datetime.date.today()
        self.assertIn('should be greater then', str(e.exception))

    def test_create_test_commission_log_simple(self):
        commission_log_obj = self.env['oi1_commission_log']
        partner_obj = self.env['res.partner']
        commission_obj = self.env['oi1_commission']
        product_obj = self.env['product.product']

        product_id = product_obj.create({'name': 'test_commission_product'})

        partner_1 = partner_obj.create({'name': "test_partner1"})
        com_partner_1 = partner_obj.create({'name': 'test_commission_partner1'})
        com_partner_2 = partner_obj.create({'name': 'test_commission_partner2'})
        model_name = 'res.partner'
        role_id = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_sales')
        start_date = datetime.date.today() - datetime.timedelta(days=7)

        commission = commission_obj.create({'commission_role_id': role_id.id,
                                            'product_id': product_id.id,
                                            })
        self.assertTrue(commission.id)

        commission_log = commission_log_obj.set_commission_log(model_name,
                                                               partner_1.id,
                                                               com_partner_1,
                                                               role_id,
                                                               start_date,
                                                               False,
                                                               4.0)
        self.assertTrue(commission_log.id)

        date = datetime.date.today()
        partners = commission_log_obj.get_commission_partner(model_name,
                                                             partner_1.id,
                                                             role_id,
                                                             date)
        self.assertTrue(len(partners) == 1)
        commission_log.unlink()
        partners = commission_log_obj.get_commission_partner(model_name,
                                                             partner_1.id,
                                                             role_id,
                                                             date)
        self.assertEqual(len(partners), 0)

        end_date = datetime.date.today() + datetime.timedelta(days=7)
        commission_log = commission_log_obj.set_commission_log(model_name,
                                                               partner_1.id,
                                                               com_partner_1,
                                                               role_id,
                                                               start_date,
                                                               end_date,
                                                               4.0)
        partners = commission_log_obj.get_commission_partner(model_name,
                                                             partner_1.id,
                                                             role_id,
                                                             date)
        self.assertEqual(len(partners), 1)

        end_date = end_date - datetime.timedelta(days=2)
        commission_log.end_date = end_date
        partners = commission_log_obj.get_commission_partner(model_name,
                                                             partner_1.id,
                                                             role_id,
                                                             date)
        self.assertEqual(len(partners), 1)
        self.assertEqual(partners.partner_id.id, com_partner_1.id)

        commission_log.end_date = False
        start_date = datetime.date.today()
        commission_log = commission_log_obj.set_commission_log(model_name,
                                                               partner_1.id,
                                                               com_partner_2,
                                                               role_id,
                                                               start_date,
                                                               False,
                                                               4.0)
        partners = commission_log_obj.get_commission_partner(model_name,
                                                             partner_1.id,
                                                             role_id,
                                                             date)
        self.assertEqual(len(partners), 1)
        self.assertEqual(partners.partner_id.id, com_partner_2.id)

        commission_log.unlink()
        partners = commission_log_obj.get_commission_partner(model_name,
                                                             partner_1.id,
                                                             role_id,
                                                             date)
        self.assertEqual(len(partners), 0)


