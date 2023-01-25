from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_sale_id = fields.Many2one('sale.order')