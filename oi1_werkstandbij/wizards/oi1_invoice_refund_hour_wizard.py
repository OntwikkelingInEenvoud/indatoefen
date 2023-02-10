from odoo import models, fields, _
from odoo.exceptions import UserError


class InvoiceRefundHourWizard(models.TransientModel):
    _name = "oi1_werkstandbij.invoice_refund_hour_wizard"
    _description = "Refund hour invoices"

    invoice_id = fields.Many2one('account.move', string="Invoices")

    def do_refund_hour_invoice(self):
        account_move_obj = self.env['account.move']
        if not self.invoice_id.id:
            raise UserError(_("Please provide an invoice"))
        invoice_id = self.invoice_id
        hour_lines = invoice_id.x_sale_account_analytic_line_ids
        if len(hour_lines) == 0:
            raise UserError(_("No hourlines found related to this invoice"))

        refund_wizard = self.env['account.move.reversal'].with_context(active_model="account.move",
                                                                       active_ids=invoice_id.id).create({
            'reason': 'Wrong hours',
            'refund_method': 'refund',
            'journal_id': invoice_id.journal_id.id,
        })
        refund_invoice_dict = refund_wizard.reverse_moves()
        if not 'res_id' in refund_invoice_dict:
            raise UserError(_(" No refund invoice created"))
        refund_invoice = account_move_obj.browse([refund_invoice_dict['res_id']])
        refund_invoice.action_post()
        refund_invoice.invoice_origin = invoice_id.name
        refund_invoice.do_prepare_payment_wsb()

        hour_lines.with_context({'system': True}).write({'x_sale_invoice_line_id': False,
                                                         'timesheet_invoice_id': False,
                                                         'x_state': 'approved'})

        pur_hour_lines = hour_lines.filtered(lambda l: l.x_pur_invoice_line_id.move_id.state == 'draft')
        pur_account_move_lines = pur_hour_lines.mapped('x_pur_invoice_line_id')
        pur_account_move_lines.with_context({"check_move_validity" : False}).unlink()
        message = _("Invoice %s is credited with invoice %s" % (invoice_id.name, refund_invoice.name))
        invoice_id.with_context({'system': True}).message_post(body=message)
