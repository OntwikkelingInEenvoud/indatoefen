from odoo import models, api, _
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'move_id' in vals:
                account_move = self.env['account.move'].browse([vals['move_id']])
                if len(account_move.invoice_origin or '') > 0:
                    sale_orders = self.env['sale.order'].search([('name','=', account_move.invoice_origin)])
                    if len(sale_orders) > 0:
                        sale_order = sale_orders[0]
                        if len(sale_orders.partner_id.vat or '') == 0 and sale_order.x_vat_inland_shifted:
                            raise ValidationError(_("Please provide a valid VAT for the partner %s of the sales order %s")
                                              % (sale_orders.partner_id.name, sale_order.name))
                        if sale_order.x_vat_inland_shifted and sale_order.company_id.id == account_move.company_id.id:
                            vals['tax_ids'] = [(6, 0, [self.env.ref('oi1_account_move_vat_shifted.account_tax_id').id])]
        self.env.context = dict(self.env.context)
        self.env.context['check_move_validity'] = False
        return super().create(vals_list)
