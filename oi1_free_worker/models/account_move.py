from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    x_freeworker_id = fields.Many2one('oi1_free_worker', related="partner_id.x_freeworker_id", string="Free worker")
    x_is_freeworker_visible = fields.Boolean(related="partner_id.x_is_freeworker_visible")

    def _compute_x_invoice_email(self):
        for account_move in self:
            super()._compute_x_invoice_email()
            if account_move.partner_id.x_is_freeworker:
                account_move.x_invoice_email = account_move.partner_id.x_communication_email
