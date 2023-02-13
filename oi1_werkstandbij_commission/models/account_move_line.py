from odoo import models, fields, api
from datetime import date


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sale_commission_payment_line_ids = fields.One2many('oi1_sale_commission_payment_line', 'pur_invoice_line_id')