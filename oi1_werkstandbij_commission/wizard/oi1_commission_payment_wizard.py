from odoo import models, _
from odoo.exceptions import UserError


class CommissionPaymentWizard(models.TransientModel):
    _name = "oi1_werkstandbij_commission.commission_payment_wizard"
    _description = "Generate invoices for commission payments"

    def do_agree_and_invoice_commissions(self):
        commission_payments = self.env['oi1_sale_commission_payment'].browse(self._context.get('active_ids', []))
        for commission_payment in commission_payments:
            if commission_payment.type == 'reservation':
                raise UserError(_('Warning commission payment %s is of type Reservation') % commission_payment.number)
            if commission_payment.state not in ('concept', 'approved'):
                raise UserError(_('Warning commission payment %s has not the right state') % commission_payment.number)
            commission_payment.do_approve()
            commission_payment.do_invoice()
        return self.env['oi1_sale_commission_payment'].do_go_to_not_paid_invoice_commission_forms(self.env)
