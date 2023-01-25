from odoo import models, fields


class InvoiceLine(models.Model):
    _inherit = 'account.move.line'
    x_qty_delivered = fields.Float(string="Qty delivered", compute="_compute_qty_delivered")
    x_nett_price_unit = fields.Monetary(string="Nett", compute="_compute_nett_amount")

    def _compute_qty_delivered(self):
        for invoice_line in self:
            qty_delivered = 0.0
            for sale_order_line in invoice_line.sale_line_ids:
                qty_delivered = qty_delivered + sale_order_line.qty_delivered
            invoice_line.x_qty_delivered = qty_delivered

    def _compute_nett_amount(self):
        for invoice_line in self:
            invoice_line.x_nett_price_unit = ((100 - invoice_line.discount)/ 100) * invoice_line.price_unit

