from odoo.tests.common import TransactionCase, tagged
from odoo import Command
from datetime import date, timedelta


@tagged('test_tools')
class TestTools(TransactionCase):
    def setUp(self, *args, **kwargs):
        result = super().setUp(*args, **kwargs)
        return result

    """
    " 2023_0106 With the use of the tools all lines of an invoice should be deleted 
                and a new one created with the same values 
    """
    def test_save_with_tools(self):
        account_move_line_obj = self.env['account.move.line']
        tools_obj = self.env['oi1.object_tools']

        list_account_move_line = account_move_line_obj.search([('display_type', '=', 'product')], limit=1)
        self.assertEqual(len(list_account_move_line), 1)

        account_move = list_account_move_line.move_id
        list_account_move_line = account_move.invoice_line_ids
        self.assertGreater(len(list_account_move_line), 0)

        list_dict = tools_obj.get_dictionary_values(list_account_move_line)
        self.assertEqual(len(list_dict), len(list_account_move_line))

        new_account_move = account_move.copy()
        new_account_move.with_context(dynamic_unlink=True).write({'line_ids': False})
        self.assertEqual(len(new_account_move.invoice_line_ids),0)

        for invoice_line_values in list_dict:
            new_account_move.with_context({'system': 1}).write({'invoice_line_ids': [Command.create(invoice_line_values)]})

        self.assertEqual(len(account_move.line_ids), len(new_account_move.line_ids))
        self.assertEqual(account_move.amount_total_signed, new_account_move.amount_total_signed)

        new_account_move.action_post()
        self.assertEqual(new_account_move.state, 'posted')

    def test_get_ids(self):
        tools_obj = self.env['oi1.object_tools']
        list_id1 = 1283
        list_id2 = 3983

        values = [(6, 0, [list_id1])]
        list_ids = tools_obj.get_id_list(values)
        self.assertEqual(len(list_ids), 1)
        self.assertEqual(list_id1, list_ids[0])

        values = [(6, 0, [list_id1, list_id2])]
        list_ids = tools_obj.get_id_list(values)
        self.assertEqual(len(list_ids), 2)
        self.assertEqual(list_id1, list_ids[0])
        self.assertEqual(list_id2, list_ids[1])

        values = [(4, [list_id1])]
        list_ids = tools_obj.get_id_list(values)
        self.assertEqual(len(list_ids), 1)
        self.assertEqual(list_id1, list_ids[0])

        values = [(4, [list_id1, list_id2])]
        list_ids = tools_obj.get_id_list(values)
        self.assertEqual(len(list_ids), 2)
        self.assertEqual(list_id1, list_ids[0])
        self.assertEqual(list_id2, list_ids[1])

        values = [(4, [list_id1]), (4, [list_id2])]
        list_ids = tools_obj.get_id_list(values)
        self.assertEqual(len(list_ids), 2)
        self.assertEqual(list_id1, list_ids[0])
        self.assertEqual(list_id2, list_ids[1])