# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from datetime import date, timedelta
from odoo import exceptions


@tagged('test_invoice_helper')
class TestAccountInvoice(TransactionCase):

    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        self.mediator_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_mediator')
        self.recruiter_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_recruiter')
        self.practical_work_planner_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_practical_work_planner')
        self.seller_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_sales')
        self.operational_work_planner_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_operational_work_planner')
        self.poule_manager_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_poule_manager')
        self.account_manager_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_account_manager')
        self.env.user.lang = False
        return result

    def test_commissions_date_selections(self):
        c_default_rate = 5.5
        product_product_obj = self.env['product.product']
        commission_partner_obj = self.env['oi1_commission_partner']
        commission_obj = self.env['oi1_commission']
        free_worker_poule_obj = self.env['oi1_freeworkerpoule']
        commission_invoice_helper_obj = self.env['oi1_commission_invoice_helper']

        product_id = product_product_obj.create({'name': 'commission_product'})

        operational_work_planner = commission_obj.create({'name': self.operational_work_planner_role.name,
                                                          'commission_role_id': self.operational_work_planner_role.id,
                                                          'product_id': product_id.id,
                                                          'default_rate': c_default_rate
                                                          })
        name = 'test_commission_partner_1'
        partner1 = self.env['res.partner'].create({'name': name})
        self.assertEqual(partner1.name, name)
        poule_name = 'test_poule'
        free_worker_poule_id = free_worker_poule_obj.create({'name': poule_name,
                                                             'act_description': 'test_omschrijving',
                                                             'product_id': product_id.id,
                                                             })
        self.assertEqual(free_worker_poule_id.name, poule_name)

        free_worker_poule_id.operational_work_planner_partner_id = partner1
        commission_partner = commission_partner_obj.create({'partner_id': partner1.id,
                                                            'commission_id': operational_work_planner.id})
        commission_logs = commission_invoice_helper_obj.get_commissions_on_poule(free_worker_poule_id)
        self.assertEqual(len(commission_logs), 1)
        commission_logs.start_date = date.today() + timedelta(days=10)
        commission_check_logs = commission_invoice_helper_obj.get_commissions_on_poule(free_worker_poule_id)
        self.assertEqual(len(commission_check_logs), 0)
        commission_logs.unlink()

        free_worker_poule_id.operational_work_planner_partner_id = partner1
        commission_logs = commission_invoice_helper_obj.get_commissions_on_poule(free_worker_poule_id)
        self.assertEqual(len(commission_logs), 1)
        commission_logs.start_date -= timedelta(days=25)
        commission_logs.end_date = date.today() - timedelta(days=15)
        commission_check_logs = commission_invoice_helper_obj.get_commissions_on_poule(free_worker_poule_id)
        self.assertEqual(len(commission_check_logs), 0)
        commission_logs.unlink()

        free_worker_poule_id.operational_work_planner_partner_id = partner1
        commission_logs = commission_invoice_helper_obj.get_commissions_on_poule(free_worker_poule_id)
        self.assertEqual(len(commission_logs), 1)
        commission_logs.end_date = date.today() + timedelta(days=15)
        commission_check_logs = commission_invoice_helper_obj.get_commissions_on_poule(free_worker_poule_id)
        #self.assertEqual(len(commission_check_logs), 1)
        commission_logs.unlink()

    def test_commissions_poule_manager(self):
        c_default_rate = 4.5
        product_product_obj = self.env['product.product']
        commission_partner_obj = self.env['oi1_commission_partner']
        commission_obj = self.env['oi1_commission']
        free_worker_poule_obj = self.env['oi1_freeworkerpoule']
        commission_invoice_helper_obj = self.env['oi1_commission_invoice_helper']

        product_id = product_product_obj.create({'name': 'commission_product'})

        operational_work_planner = commission_obj.create({'name': self.operational_work_planner_role.name,
                                                   'commission_role_id': self.operational_work_planner_role.id,
                                                   'product_id': product_id.id,
                                                   'default_rate': c_default_rate
                                                   })
        poule_manager_role = commission_obj.create({'name': self.poule_manager_role.name,
                                                          'commission_role_id': self.poule_manager_role.id,
                                                          'product_id': product_id.id,
                                                          'default_rate': c_default_rate
                                                          })

        name = 'test_commission_partner_1'
        partner1 = self.env['res.partner'].create({'name': name})
        self.assertEqual(partner1.name, name)
        name = 'test_commission_partner_2'
        partner2 = self.env['res.partner'].create({'name': name})
        self.assertEqual(partner2.name, name)
        poule_name = 'test_poule'
        free_worker_poule_id = free_worker_poule_obj.create({'name': poule_name,
                                                             'act_description': 'test_omschrijving',
                                                             'product_id': product_id.id,
                                                             })
        self.assertEqual(free_worker_poule_id.name, poule_name)

        free_worker_poule_id.operational_work_planner_partner_id = partner1
        free_worker_poule_id.poule_manager_partner_id = partner2

        commission_partner = commission_partner_obj.create({'partner_id': partner1.id,
                                                            'commission_id': operational_work_planner.id})

        commission_partner1 = commission_partner_obj.create({'partner_id': partner2.id,
                                                            'commission_id': poule_manager_role.id})

        commission_mains = commission_invoice_helper_obj.get_commissions_on_poule(free_worker_poule_id)
        self.assertEqual(len(commission_mains), 2)
        check_commissions = commission_mains.filtered(lambda l: l.commission_main_id.commission_id.id == operational_work_planner.id)
        self.assertEqual(len(check_commissions), 1)
        self.assertEqual(check_commissions.partner_id.id, partner1.id)
        check_commissions = commission_mains.filtered(lambda l: l.commission_main_id.commission_id.id == poule_manager_role.id)
        self.assertEqual(len(check_commissions), 1)
        self.assertEqual(check_commissions.partner_id.id, partner2.id)

    def test_commissions_free_worker(self):
        c_default_rate = 3.5
        product_product_obj = self.env['product.product']
        commission_free_worker_obj = self.env['oi1_commission_free_worker']
        commission_obj = self.env['oi1_commission']
        commission_invoice_helper_obj = self.env['oi1_commission_invoice_helper']
        free_worker_obj = self.env['oi1_free_worker']

        product_id = product_product_obj.create({'name': 'commission_product'})
        free_worker = free_worker_obj.create({'name': 'free_worker'})

        commission_free_worker = commission_free_worker_obj.create({'free_worker_id': free_worker.id,
                                                            })
        commission_mains = commission_invoice_helper_obj.get_free_worker_commissions()
        self.assertEqual(len(commission_mains), 1)
        self.assertEqual(commission_mains.partner_id.id, free_worker.partner_id.id)
        commission_free_worker.start_date = date.today() + timedelta(days=25)
        commission_mains = commission_invoice_helper_obj.get_free_worker_commissions()
        self.assertEqual(len(commission_mains), 0)
        commission_free_worker.start_date = date.today() - timedelta(days=25)
        commission_mains = commission_invoice_helper_obj.get_free_worker_commissions()
        self.assertEqual(len(commission_mains), 1)
        commission_free_worker.end_date = date.today() - timedelta(days=10)
        commission_mains = commission_invoice_helper_obj.get_free_worker_commissions()
        self.assertEqual(len(commission_mains), 0)
        commission_free_worker.end_date = date.today() + timedelta(days=10)
        commission_mains = commission_invoice_helper_obj.get_free_worker_commissions()
        self.assertEqual(len(commission_mains), 1)

    def test_commissions_sale_order(self):
        c_default_rate = 3.5
        product_product_obj = self.env['product.product']
        commission_partner_obj = self.env['oi1_commission_partner']
        commission_obj = self.env['oi1_commission']
        sale_order_obj = self.env['sale.order']
        commission_invoice_helper_obj = self.env['oi1_commission_invoice_helper']
        partner_obj = self.env['res.partner']

        product_id = product_product_obj.create({'name': 'commission_product'})

        commission_seller = commission_obj.create({'name': self.seller_role.name,
                                                     'commission_role_id': self.seller_role.id,
                                                     'product_id': product_id.id,
                                                     'default_rate': c_default_rate
                                                     })
        name = 'test_commission_partner_1'
        partner1 = partner_obj.create({'name': name})
        self.assertEqual(partner1.name, name)
        sale_order_id = sale_order_obj.create({'partner_id': partner1.id})
        self.assertEqual(sale_order_id.partner_id.id, partner1.id)

        sale_order_id.x_seller_partner_id = partner1
        commission_partner_obj.create({'partner_id': partner1.id,
                                       'commission_id': commission_seller.id})
        commission_mains = commission_invoice_helper_obj.get_commissions_on_sale_order(sale_order_id)
        self.assertEqual(len(commission_mains), 1)
        check_commissions = commission_mains.filtered(lambda l: l.commission_main_id.commission_id.id == commission_seller.id)
        self.assertEqual(len(check_commissions), 1)
        self.assertEqual(check_commissions.partner_id.id, partner1.id)

        commission_account_manager = commission_obj.create({'name': self.seller_role.name,
                                                     'commission_role_id': self.account_manager_role.id,
                                                     'product_id': product_id.id,
                                                     'default_rate': c_default_rate
                                                     })
        name = 'test_commission_partner_2'
        partner2 = partner_obj.create({'name': name})
        self.assertEqual(partner2.name, name)
        sale_order_id.x_account_manager_partner_id = partner2
        commission_partner_obj.create({'partner_id': partner2.id,
                                       'commission_id': commission_account_manager.id})
        commission_mains = commission_invoice_helper_obj.get_commissions_on_sale_order(sale_order_id)
        self.assertEqual(len(commission_mains), 2)
        check_commissions = commission_mains.filtered(lambda l: l.commission_main_id.commission_id.id == commission_account_manager.id)
        self.assertEqual(len(check_commissions), 1)
        self.assertEqual(check_commissions.partner_id.id, partner2.id)

        name = 'test_klant_1'
        partner3 = partner_obj.create({'name': name})
        partner3.x_account_manager_partner_id = partner2
        partner3.x_seller_partner_id = partner1
        sale_order_id = sale_order_obj.create({'partner_id': partner3.id})
        commission_mains = commission_invoice_helper_obj.get_commissions_on_sale_order(sale_order_id)
        self.assertEqual(len(commission_mains), 2)



    def test_commissions_free_worker(self):
        c_default_rate = 2.5

        commission_partner_obj = self.env['oi1_commission_partner']
        commission_obj = self.env['oi1_commission']
        product_product_obj = self.env['product.product']
        commission_invoice_helper_obj = self.env['oi1_commission_invoice_helper']
        free_worker_obj = self.env['oi1_free_worker']

        free_worker = free_worker_obj.create({'name': 'free_worker'})
        product_id = product_product_obj.create({'name': 'commission_product'})

        commission_mediator = commission_obj.create({'name': self.mediator_role.name,
                                            'commission_role_id': self.mediator_role.id,
                                            'product_id': product_id.id,
                                            'default_rate': c_default_rate
                                            })
        self.assertEqual(commission_mediator.name, self.mediator_role.name)
        self.assertEqual(commission_mediator.default_rate, c_default_rate)

        commission_recruiter = commission_obj.create({'name': self.recruiter_role.name,
                                                     'commission_role_id': self.recruiter_role.id,
                                                     'product_id': product_id.id,
                                                     'default_rate': c_default_rate
                                                     })
        self.assertEqual(commission_recruiter.name, self.recruiter_role.name)
        self.assertEqual(commission_mediator.default_rate, c_default_rate)

        commission_practical_work_planner = commission_obj.create({'name': self.practical_work_planner_role.name,
                                                      'commission_role_id': self.practical_work_planner_role.id,
                                                      'product_id': product_id.id,
                                                      'default_rate': c_default_rate
                                                      })
        self.assertEqual(commission_practical_work_planner.name, self.practical_work_planner_role.name)
        self.assertEqual(commission_practical_work_planner.default_rate, c_default_rate)

        name = 'test_commission_partner_1'
        partner1 = self.env['res.partner'].create({'name': name})
        self.assertEqual(partner1.name, name)
        name = 'test_commission_partner_2'
        partner2 = self.env['res.partner'].create({'name': name})
        self.assertEqual(partner2.name, name)
        name = 'test_commission_partner_3'
        partner3 = self.env['res.partner'].create({'name': name})
        self.assertEqual(partner3.name, name)

        commission_partner = commission_partner_obj.create({'partner_id': partner1.id,
                                                            'commission_id': commission_mediator.id})
        commission_partner2 = commission_partner_obj.create({'partner_id': partner2.id,
                                                            'commission_id': commission_recruiter.id})
        commission_partner3 = commission_partner_obj.create({'partner_id': partner3.id,
                                                             'commission_id': commission_practical_work_planner.id})

        self.assertEqual(commission_partner.default_rate, c_default_rate)
        self.assertEqual(len(partner1.x_oi1_commission_partner_ids), 1)

        free_worker.mediator_partner_id = partner1
        self.assertEqual(free_worker.mediator_partner_id.id, partner1.id)

        free_worker.recruiter_partner_id = partner2
        self.assertEqual(free_worker.recruiter_partner_id.id, partner2.id)

        free_worker.practical_work_planner_partner_id = partner3
        self.assertEqual(free_worker.practical_work_planner_partner_id.id, partner3.id)

        commission_mains = commission_invoice_helper_obj.get_commissions_on_free_worker(free_worker)
        self.assertEqual(len(commission_mains), 3)

        check_commissions = commission_mains.filtered(lambda l: l.commission_main_id.commission_id.id == commission_mediator.id)
        self.assertEqual(len(check_commissions), 1)
        self.assertEqual(check_commissions.partner_id.id, partner1.id)

        check_commissions = commission_mains.filtered(lambda l: l.commission_main_id.commission_id.id == commission_recruiter.id)
        self.assertEqual(len(check_commissions), 1)
        self.assertEqual(check_commissions.partner_id.id, partner2.id)

        check_commissions = commission_mains.filtered(lambda l: l.commission_main_id.commission_id.id == commission_practical_work_planner.id)
        self.assertEqual(len(check_commissions), 1)
        self.assertEqual(check_commissions.partner_id.id, partner3.id)

    def test_commission_in_sub_commissions(self):
        c_default_rate = 3.5
        commission_obj = self.env['oi1_commission']
        commission_partner_obj = self.env['oi1_commission_partner']
        product_product_obj = self.env['product.product']
        commission_invoice_helper_obj = self.env['oi1_commission_invoice_helper']

        product_id = product_product_obj.create({'name': 'commission_product'})
        commission_mediator = commission_obj.create({'name': self.mediator_role.name,
                                                     'commission_role_id': self.mediator_role.id,
                                                     'product_id': product_id.id,
                                                     'default_rate': c_default_rate
                                                     })
        name = 'test_commission_partner_1'
        partner1 = self.env['res.partner'].create({'name': name})
        commission_partner = commission_partner_obj.create({'partner_id': partner1.id,
                                                            'commission_id': commission_mediator.id})
        commission_main = commission_partner.main_id

        commission_main = commission_invoice_helper_obj.split_commission_in_sub_commissions(commission_main)
        self.assertTrue(len(commission_main)) == 1

        sub_commission = commission_obj.create({'name': self.mediator_role.name,
                                                     'product_id': product_id.id,
                                                     'default_rate': c_default_rate - 1
                                                     })
        commission_mediator.write({"sub_commission_ids": [(6, 0, [sub_commission.id])]})
        commission_mains = commission_invoice_helper_obj.split_commission_in_sub_commissions(commission_main)
        self.assertEqual(len(commission_mains), 2)

        amount = 0.0
        for sub_commission_main in commission_mains:
            amount += sub_commission_main.calculation_rate
        self.assertEqual(c_default_rate, amount)

        sub_commission.default_rate = c_default_rate + 1
        commission_mains = commission_invoice_helper_obj.split_commission_in_sub_commissions(commission_main)
        with self.assertRaises(exceptions.UserError) as e:
            for commission_main in commission_mains:
                amount += commission_main.calculation_rate
        self.assertIn("the amount of the subcommissions is higher then the commission amount", str(e.exception))