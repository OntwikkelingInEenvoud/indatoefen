# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo import api


@tagged('oi1', 'test_commission_reservation')
class TestCommissionReservation(TransactionCase):
    CONST_cHourUnitAmount1 = 7
    CONST_cHourUnitAmount2 = 5

    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        self.env.user.lang = False
        return result

    def test_set_up_data(self):
        test_company_id = 1

        sale_order_obj = self.env['sale.order']
        partner_obj = self.env['res.partner']
        sale_order_line_obj = self.env['sale.order.line']
        free_worker_obj = self.env['oi1_free_worker']
        commission_obj = self.env['oi1_commission']
        product_product_obj = self.env['product.product']

        product_list = product_product_obj.search([], limit=1)
        self.assertEqual(len(product_list), 1)

        payment_term_obj = self.env['account.payment.term']

        self.company_id = self.env['res.company'].browse([test_company_id])

        account_manager_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_account_manager')
        poule_manager_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_poule_manager')

        self.assertTrue(poule_manager_role.id)
        self.assertTrue(account_manager_role.id)

        commission_list = commission_obj.search([('commission_role_id','=', account_manager_role.id)])
        commission_list.write({'active': False})

        commission_list = commission_obj.search([('commission_role_id', '=', poule_manager_role.id)])
        commission_list.write({'active': False})

        commission_obj.create({'name':'test accountmanager commission',
                               'commission_role_id': account_manager_role.id,
                               'product_id': product_list[0].id
                               })
        commission_obj.create({'name': 'test poulemanager commission',
                               'commission_role_id': poule_manager_role.id,
                               'product_id': product_list[0].id
                               })

        payment_term = payment_term_obj.search([('company_id', 'in', (self.company_id.id, False))])[0]

        self.free_worker_poule_commission = free_worker_obj.create({'name': 'test free worker'})
        self.free_worker_book = free_worker_obj.create({'name': 'test free worker book'})
        self.account_manager_partner_id = partner_obj.create({'name': 'test account manager'})



        vrije_werker_product_template = self.env.ref('oi1_werkstandbij.product_template_free_workers_poule')
        self.assertTrue(vrije_werker_product_template.id)
        self.customer = partner_obj.create({'name': 'test_customer'})
        self.assertTrue(self.customer.id)
        self.sale_order = sale_order_obj.create({'partner_id': self.customer.id,
                                                 'payment_term_id': payment_term.id,
                                                 'name': 'test order reservation'})
        self.assertTrue(self.sale_order.id)

        self.sale_order.x_account_manager_partner_id = self.account_manager_partner_id
        self.sale_order.x_account_manager_partner_id_amount = 1

        sale_order_line = sale_order_line_obj.create({'order_id': self.sale_order.id,
                                                      'product_id': vrije_werker_product_template.product_variant_id.id,
                                                      'x_price': 25.0
                                                      })

        self.assertTrue(sale_order_line.id)
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.state == 'sale')
        self.assertTrue(len(self.sale_order.x_poule_ids) == 1)
        self.free_worker_poule = self.sale_order.x_poule_ids[0]
        self.assertTrue(self.free_worker_poule.id)
        self.account_analytic_line = self.get_hour_bookline(TestCommissionReservation.CONST_cHourUnitAmount1)
        self.assertTrue(self.account_analytic_line.id)

    @api.model
    def get_hour_bookline(self, unit_amount):
        account_analytic_line_obj = self.env['account.analytic.line']
        return account_analytic_line_obj.create(
            {'x_partner_id': self.free_worker_book.partner_id.id,
             'x_sale_id': self.sale_order.id,
             'project_id': self.free_worker_poule.project_id.id,
             'x_from_time': '09:00',
             'x_to_time': '17:00',
             'x_pause_time': '01:00',
             'unit_amount': unit_amount
             })

    @api.model
    def process_hours(self, ids):
        account_invoice_obj = self.env['account.move']
        agree_hour_line_wizard_obj = self.env['oi1_werkstandbij.agreehourline_wizard']

        wizard = agree_hour_line_wizard_obj.create({})
        wizard.with_context({"active_ids": ids}).do_create_agreements_and_invoice()
        self.invoices = account_invoice_obj.search([('partner_id', '=', self.customer.id)])
        self.assertEqual(len(self.invoices), 1)
        self.invoices.do_prepare_payment_wsb()

    def test_commission_reservation_poule(self):
        self.test_set_up_data()
        sale_commission_payment_obj = self.env['oi1_sale_commission_payment']

        const_poule_manager_partner_id_amount = 1.00
        const_poule_manager_partner_id_amount_reservation = 0.25
        self.free_worker_poule.poule_manager_partner_id = self.free_worker_poule_commission.partner_id
        self.free_worker_poule.poule_manager_partner_id_amount = const_poule_manager_partner_id_amount
        self.free_worker_poule.reservation_amount = const_poule_manager_partner_id_amount_reservation

        self.process_hours([self.account_analytic_line.id])

        sale_commission_payments = sale_commission_payment_obj.search(
            [('partner_id', '=', self.account_manager_partner_id.id)])
        self.assertEqual(len(sale_commission_payments), 1)

        sale_commission_payments = sale_commission_payment_obj.search(
            [('partner_id', '=', self.free_worker_poule_commission.partner_id.id)])

        self.assertEqual(len(sale_commission_payments), 2)

        sale_commission_payments = sale_commission_payments.filtered(lambda l: l.type == 'commission')
        self.assertEqual(len(sale_commission_payments), 1)

        sale_commission_payment = sale_commission_payments[0]

        sale_commission_payment_lines = sale_commission_payment.sale_commission_payment_lines
        self.assertEqual(len(sale_commission_payment_lines), 1)

        self.assertEqual(sale_commission_payment_lines.qty, TestCommissionReservation.CONST_cHourUnitAmount1)
        self.assertEqual(sale_commission_payment_lines.rate,
                          const_poule_manager_partner_id_amount - const_poule_manager_partner_id_amount_reservation)

        self.assertEqual(sale_commission_payment.amount, (TestCommissionReservation.CONST_cHourUnitAmount1 * const_poule_manager_partner_id_amount) - (
                TestCommissionReservation.CONST_cHourUnitAmount1 * const_poule_manager_partner_id_amount_reservation))

        sale_commission_payment_reservations = sale_commission_payment_obj.with_context(active_test=False).search(
            [('partner_id', '=', self.free_worker_poule_commission.partner_id.id),
             ('type', '=', 'reservation')
             ])
        self.assertEqual(len(sale_commission_payment_reservations), 1)

        sale_commission_payment_reservation = sale_commission_payment_reservations[0]
        self.assertEqual(sale_commission_payment_reservation.amount,
                           TestCommissionReservation.CONST_cHourUnitAmount1 * const_poule_manager_partner_id_amount_reservation)

    def test_commission_reservation_order(self):
        self.test_set_up_data()
        sale_commission_payment_obj = self.env['oi1_sale_commission_payment']

        const_sale_manager_partner_id_amount = 1.00
        const_sale_manager_partner_id_amount_reservation = 0.25

        self.sale_order.x_account_manager_partner_id = self.free_worker_poule_commission.partner_id
        self.sale_order.x_account_manager_partner_id_amount = const_sale_manager_partner_id_amount
        self.sale_order.x_reservation_amount = const_sale_manager_partner_id_amount_reservation

        self.process_hours([self.account_analytic_line.id])

        sale_commission_payments = sale_commission_payment_obj.search(
            [('partner_id', '=', self.free_worker_poule_commission.partner_id.id)])

        self.assertEqual(len(sale_commission_payments), 2)

        sale_commission_payments = sale_commission_payments.filtered(lambda l: l.type == 'commission')
        self.assertEqual(len(sale_commission_payments), 1)

        sale_commission_payment = sale_commission_payments[0]

        sale_commission_payment_lines = sale_commission_payment.sale_commission_payment_lines
        self.assertEqual(len(sale_commission_payment_lines), 1)

        self.assertEqual(sale_commission_payment_lines.qty, TestCommissionReservation.CONST_cHourUnitAmount1)
        self.assertEqual(sale_commission_payment_lines.rate,
                          const_sale_manager_partner_id_amount - const_sale_manager_partner_id_amount_reservation)

        self.assertEqual(sale_commission_payment.amount,
                          (TestCommissionReservation.CONST_cHourUnitAmount1 * const_sale_manager_partner_id_amount) - (
                                  TestCommissionReservation.CONST_cHourUnitAmount1 * const_sale_manager_partner_id_amount_reservation))

        sale_commission_payment_reservations = sale_commission_payment_obj.with_context(active_test=False).search(
            [('partner_id', '=', self.free_worker_poule_commission.partner_id.id),
             ('type', '=', 'reservation')
             ])
        self.assertEqual(len(sale_commission_payment_reservations), 1)

        sale_commission_payment_reservation = sale_commission_payment_reservations[0]
        self.assertEqual(sale_commission_payment_reservation.amount,
                          7 * const_sale_manager_partner_id_amount_reservation)

    def test_commission_reservation_order_multiple(self):
        self.test_set_up_data()
        sale_commission_payment_obj = self.env['oi1_sale_commission_payment']

        const_sale_manager_partner_id_amount = 1.00
        const_sale_manager_partner_id_amount_reservation = 0.25

        self.sale_order.x_account_manager_partner_id = self.free_worker_poule_commission.partner_id
        self.sale_order.x_account_manager_partner_id_amount = const_sale_manager_partner_id_amount
        self.sale_order.x_reservation_amount = const_sale_manager_partner_id_amount_reservation

        account_analytic_line = self.get_hour_bookline(TestCommissionReservation.CONST_cHourUnitAmount2)

        self.process_hours([self.account_analytic_line.id, account_analytic_line.id])

        sale_commission_payments = sale_commission_payment_obj.search(
            [('partner_id', '=', self.free_worker_poule_commission.partner_id.id)])

        self.assertEqual(len(sale_commission_payments), 2)

        sale_commission_payments = sale_commission_payments.filtered(lambda l: l.type == 'commission')
        self.assertEqual(len(sale_commission_payments), 1)

        sale_commission_payment = sale_commission_payments[0]

        sale_commission_payment_lines = sale_commission_payment.sale_commission_payment_lines.sorted(key=lambda r: -r.qty)
        self.assertEqual(len(sale_commission_payment_lines), 2)
        qty = 0
        total_hours = TestCommissionReservation.CONST_cHourUnitAmount1 + TestCommissionReservation.CONST_cHourUnitAmount2

        for sale_commission_payment_line in sale_commission_payment_lines:
            qty += sale_commission_payment_line.qty
        self.assertEqual(qty, total_hours)
        self.assertEqual(sale_commission_payment_lines[0].rate,
                          const_sale_manager_partner_id_amount - const_sale_manager_partner_id_amount_reservation)
        self.assertEqual(sale_commission_payment_lines[0].amount,
                          TestCommissionReservation.CONST_cHourUnitAmount1 * sale_commission_payment_lines[0].rate)

        self.assertEqual(sale_commission_payment_lines[1].rate,
                          const_sale_manager_partner_id_amount - const_sale_manager_partner_id_amount_reservation)
        self.assertEqual(sale_commission_payment_lines[1].amount,
                          TestCommissionReservation.CONST_cHourUnitAmount2 * sale_commission_payment_lines[1].rate)


        self.assertEqual(sale_commission_payment.amount,
                          (total_hours
                           * const_sale_manager_partner_id_amount) - (
                                  total_hours * const_sale_manager_partner_id_amount_reservation))

        sale_commission_payment_reservations = sale_commission_payment_obj.with_context(active_test=False).search(
            [('partner_id', '=', self.free_worker_poule_commission.partner_id.id),
             ('type', '=', 'reservation')
             ])
        self.assertEqual(len(sale_commission_payment_reservations), 1)

        sale_commission_payment_reservation = sale_commission_payment_reservations[0]
        self.assertEqual(sale_commission_payment_reservation.amount,
                          total_hours * const_sale_manager_partner_id_amount_reservation)


