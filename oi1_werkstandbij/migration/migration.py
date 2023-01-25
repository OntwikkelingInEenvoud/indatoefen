from odoo import models


class Migration(models.TransientModel):
    _name = 'oi1_werkstandbij.migration'
    _description = 'Migration tools WSB'

    def do_correction_migration_hour_lines(self):
        account_analytic_line_obj = self.env['account.analytic.line']
        hour_lines = account_analytic_line_obj.search([('create_date', '>', '2021-02-21')])
        hour_lines = hour_lines.filtered(lambda l: not l.x_commission_created)
        #wizard_obj.do_process_commissions(hour_lines, True, False)

    def do_correction_commissions_not_processed_on_invoice(self):
        account_move_obj = self.env['account.move']
        wizard_obj = self.env['oi1_werkstandbij.invoice_wizard']

        account_move = account_move_obj.search([('name', '=', 'F/2021/0420')])
        account_analytic_lines = account_move.x_sale_account_analytic_line_ids
        wizard_obj.create_commissions(account_analytic_lines)


