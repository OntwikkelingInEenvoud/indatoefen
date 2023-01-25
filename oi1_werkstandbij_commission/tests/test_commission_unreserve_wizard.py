# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import  UserError

@tagged('test_commission_unreserve_wizard')
class TestCommissionUnReserve(TransactionCase):

    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        self.env.user.lang = False
        return result

    def test_unreserve_wizard(self):

        const_sale_commission_line_amount = 35.65
        const_sale_commission_line_payment_amount = 15
        const_sale_commission_line_payment_amount_2 = 10
        const_sale_commission_line_payment_amount_3 = 10


        commission_payment_obj = self.env['oi1_sale_commission_payment']
        commission_payment_line_obj = self.env['oi1_sale_commission_payment_line']
        commission_obj = self.env['oi1_commission']
        product_product_obj = self.env['product.product']
        unreserve_wizard_obj = self.env['oi1_sale_commission_unreserve_wizard']
        invoice_obj = self.env['account.move']

        partner_obj = self.env['res.partner']

        self.partner_id  = partner_obj.create({'name': 'test_commissie_gebruiker'})

        commission_payment  = commission_payment_obj.create({'partner_id': self.partner_id.id,
                                                             'name': "test commssie",
                                                             })
        self.assertTrue(commission_payment.id)

        product_id = product_product_obj.create({'name': 'test product'})
        self.assertTrue(product_id.id)

        commission_id  = commission_obj.create({'name': 'test commission', 'product_id': product_id.id})
        self.assertTrue(commission_id.id)

        commission_payment_line = commission_payment_line_obj.create({'oi1_sale_commission_id': commission_payment.id,
                                                                       'commission_id': commission_id.id,
                                                                       'unit' : 'qty',
                                                                       'qty': 3.0,
                                                                       'rate': 5.45,
                                                                       'amount': const_sale_commission_line_amount,
                                                                       })
        self.assertTrue(commission_payment_line.id)

        unreserve_wizard = unreserve_wizard_obj.create({})
        unreserve_wizard.oi1_sale_commission_id = commission_payment
        unreserve_wizard.amount = 4.0

        with self.assertRaises(UserError) as e:
            unreserve_wizard.do_create_un_reservation()
        self.assertIn("provide aan description", str(e.exception))
        unreserve_wizard.name = "01234567891011"

        with self.assertRaises(UserError) as e:
            unreserve_wizard.do_create_un_reservation()
        self.assertIn("Unreservations can only be made on commission", str(e.exception))
        commission_payment_line.type = 'reservation'

        with self.assertRaises(UserError) as e:
            unreserve_wizard.do_create_un_reservation()
        self.assertIn("type reservation", str(e.exception))

        self.assertEqual(len(commission_payment.sale_commission_payment_lines), 1)

        commission_payment.type = 'reservation'
        unreserve_wizard.amount = 250
        with self.assertRaises(UserError) as e:
            unreserve_wizard.do_create_un_reservation()
        self.assertIn("You can not unreserve more", str(e.exception))

        self.assertEqual(len(commission_payment.sale_commission_payment_lines), 1)

        unreserve_wizard.amount = const_sale_commission_line_payment_amount

        with self.assertRaises(UserError) as e:
            unreserve_wizard.do_create_un_reservation()
        self.assertIn("should have the state approved", str(e.exception))

        commission_payment.state = 'approved'
        unreserve_wizard.do_create_un_reservation()

        self.assertEqual(len(commission_payment.sale_commission_payment_lines), 2)
        self.assertEqual(commission_payment.amount, const_sale_commission_line_amount - const_sale_commission_line_payment_amount)

        direct_payment_lines = commission_payment.sale_commission_payment_lines.filtered(lambda l: l.type == 'payment')
        self.assertEqual(len(direct_payment_lines), 1)
        self.assertEqual(direct_payment_lines[0].amount, -const_sale_commission_line_payment_amount)

        payed_amount = const_sale_commission_line_amount - (const_sale_commission_line_payment_amount + const_sale_commission_line_payment_amount_2)

        unreserve_wizard.amount = const_sale_commission_line_payment_amount_2
        unreserve_wizard.do_create_un_reservation()
        self.assertEqual(len(commission_payment.sale_commission_payment_lines), 3)
        self.assertEqual(commission_payment.amount, payed_amount)
        direct_payment_lines = commission_payment.sale_commission_payment_lines.filtered(lambda l: l.type == 'payment')
        self.assertEqual(len(direct_payment_lines), 2)
        commission_payment.do_invoice()

        invoice = invoice_obj.search([('partner_id', '=', self.partner_id.id)])

        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.amount_untaxed, const_sale_commission_line_payment_amount + const_sale_commission_line_payment_amount_2)

        unreserve_wizard.amount = const_sale_commission_line_payment_amount_3
        unreserve_wizard.do_create_un_reservation()
        direct_payment_lines = commission_payment.sale_commission_payment_lines.filtered(lambda l: l.type == 'payment')
        self.assertEqual(len(direct_payment_lines), 3)
        payed_amount = payed_amount - const_sale_commission_line_payment_amount_3
        self.assertEqual(commission_payment.amount, payed_amount)
        commission_payment.do_invoice()
        invoice = invoice_obj.search([('partner_id', '=', self.partner_id.id)])
        self.assertEqual(invoice.amount_untaxed,
                          const_sale_commission_line_payment_amount +
                          const_sale_commission_line_payment_amount_2 +
                          const_sale_commission_line_payment_amount_3
                          )
        self.assertEqual(len(invoice), 1)