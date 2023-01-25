from odoo import models, fields


class SaleOrder(models.Model):

    _inherit = 'sale.order'        
    x_invoice_line_ids  = fields.One2many('account.move.line', 'x_sale_id');