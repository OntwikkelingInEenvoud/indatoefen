from odoo.tests.common import TransactionCase, tagged
from odoo import Command
from datetime import date, timedelta


@tagged('test_export_wsb_wizard')
class TestTools(TransactionCase):
    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        self.env.user.lang = False
        test_company_id = 1
        self.env.user.lang = False
        self.seller_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_sales')

        sale_obj = self.env['sale.order']
        product_obj = self.env['product.template']
        partner_obj = self.env['res.partner']
        poule_obj = self.env['oi1_freeworkerpoule']
        commission_obj = self.env['oi1_commission']
        payment_term_obj = self.env['account.payment.term']
        free_worker_obj = self.env['oi1_free_worker']
        account_analytic_line_obj = self.env['account.analytic.line']
        sale_order_line_obj = self.env['sale.order.line']
        commission_partner_obj = self.env['oi1_commission_partner']
        agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']
        account_move_obj = self.env['account.move']

        self.partner_commission_seller = partner_obj.create({'name': 'commission_seller'})

        commission_product_id = product_obj.create({'name': 'commission product id'})

        commission_seller = commission_obj.create({'name': self.seller_role.name,
                                                   'commission_role_id': self.seller_role.id,
                                                   'product_id': commission_product_id.id,
                                                   'default_rate': 0.10
                                                   })
        commission_partner_obj.create({'partner_id': self.partner_commission_seller.id,
                                       'commission_id': commission_seller.id})

        self.company_id = self.env['res.company'].browse([test_company_id])
        payment_term = payment_term_obj.search([('company_id', 'in', (self.company_id.id, False))])[0]

        self.free_worker = free_worker_obj.create({'x_name': 'test freeworker'})

        self.product = product_obj.create({'name': 'test_product', 'type': 'service'})
        self.com_product = product_obj.create({'name': 'com_product'})
        self.commission = commission_obj.create(
            {'name': 'test commission', 'product_id': self.com_product.product_variant_id.id})

        poules = poule_obj.search([('name', '=', 'test poule')])
        for poule in poules:
            poule.active = False

        self.poule = poule_obj.create({'name': 'test poule',
                                       'act_description': 'test activiteit',
                                       'product_id': self.product.product_variant_id.id})

        self.customer = partner_obj.create({'name': ' test work provider'})
        self.com_partner = partner_obj.create({'name': ' test commission receiver'})
        self.sale_order = sale_obj.create({'partner_id': self.customer.id,
                                           'x_poule_id': self.poule.id,
                                           'payment_term_id': payment_term.id})
        self.sale_order.x_seller_partner_id = self.partner_commission_seller

        self.sale_order_line = sale_order_line_obj.create({'order_id': self.sale_order.id,
                                                           'product_id': self.product.id,
                                                           'x_price': 15,
                                                           })
        self.poule.project_id.write({'sale_line_id': self.sale_order_line,
                                     'sale_order_id': self.sale_order_line.order_id.id})

        self.hour_line = account_analytic_line_obj.create({
            'x_partner_id': self.free_worker.partner_id.id,
            'x_sale_id': self.sale_order.id,
            'x_from_time': "08:00",
            'x_to_time': "17:00",
            'x_pause_time': "02:00",
            'project_id': self.poule.project_id.id,
            'unit_amount': 7.0,
            'x_rate': 15.00
        })

        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": [self.hour_line.id]}).do_create_agreements_and_invoice()
        self.account_move = account_move_obj.search([('partner_id', '=', self.customer.id)])[0]
        return result

    def test_save_with_tools(self):
       wizard_obj = self.env['oi1_werkstandbij.export_wsb_wizard']

       wizard = wizard_obj.create({})
       wizard.path = "/media/sf_Uitwissel"

       self.account_move.do_prepare_payment_wsb()

       self.assertEqual(self.account_move.state, 'Start_Factoring')

       wizard.set_export_to_wsb()
       print("test nog verder maken")