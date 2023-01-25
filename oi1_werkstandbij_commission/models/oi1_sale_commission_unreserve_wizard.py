from odoo import models, fields, _, api
from odoo.exceptions import UserError


class UnReserveWizard(models.TransientModel):
    _name = "oi1_sale_commission_unreserve_wizard"
    _description = "Create payments from the reservations"

    @api.model
    def _default_oi1_sale_commission_id(self):
        if self._context.get('active_model') == 'oi1_sale_commission_payment' and self._context.get('active_id', False):
            return self.env['oi1_sale_commission_payment'].browse(self._context.get('active_id'))

    number = fields.Char(related="oi1_sale_commission_id.number")
    oi1_sale_commission_id = fields.Many2one('oi1_sale_commission_payment', default=_default_oi1_sale_commission_id)
    amount = fields.Monetary(string="Unit Price", default=0.0, help="The amount of the payment")
    currency_id = fields.Many2one('res.currency', related='oi1_sale_commission_id.currency_id')
    name = fields.Char(string="Description of the payment", help="Provides the description or reason of the payment")


    def do_create_un_reservation(self):
        for wizard in self:
            if wizard.amount <= 0.0:
                raise UserError(_('You should provide a positive amount'))
            if not wizard.oi1_sale_commission_id.id:
                raise UserError(_('There is no commission provided'))
            sale_commission_id = wizard.oi1_sale_commission_id
            amount = wizard.amount
            name = wizard.name
            if not name or len(name) < 10:
                raise UserError(_('Please provide aan description with is longer then 10 characters'))
            if len(sale_commission_id.sale_commission_payment_lines.filtered(lambda l: l.type == 'commission')) > 0:
               raise UserError(_('Unreservations can only be made on commission which only contains reservations'))
            if sale_commission_id.type != 'reservation':
                raise UserError(_('Unreservations can only be made on commission of type reservation'))
            if amount > sale_commission_id.amount:
                raise UserError(_('You can not unreserve more amount  %s than the reserved amount %s')
                                % (amount, sale_commission_id.amount))
            if sale_commission_id.state != 'approved':
                raise UserError(_('The commission %s should have the state approved for making unreservations') % sale_commission_id.name)
            self._add_unreservation_line(sale_commission_id, amount, name)
            sale_commission_id.do_invoice()
        return self.env['oi1_sale_commission_payment'].do_go_to_not_paid_invoice_commission_forms(self.env)

    def _add_unreservation_line(self, sale_commission_id, amount, name):
        sale_commission_line_obj = self.env['oi1_sale_commission_payment_line']
        commission_id = self.env.ref('oi1_werkstandbij.oi1_commission_reservation')

        values = {'oi1_sale_commission_id': sale_commission_id.id, 'qty': -1, 'rate': amount, 'amount': -amount,
                  'commission_id': commission_id.id, 'unit': 'qty', 'type': 'payment', 'name': name}

        return sale_commission_line_obj.create(values)



