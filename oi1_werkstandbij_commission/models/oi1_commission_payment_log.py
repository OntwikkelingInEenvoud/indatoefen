from odoo import models, fields, api, _


class CommissionPaymentLog(models.Model):
    _name = "oi1_commission_payment_log"
    _description = "Commission hour payment log"

    account_analytic_account_id = fields.Many2one('account.analytic.line', required=True, string="Hour line",
                                                  ondelete="restrict")
    calculated_rate = fields.Monetary(string="Rate", compute="_compute_calculated_rate", store=True)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id, required=True, ondelete="restrict")
    commission_log_id = fields.Many2one('oi1_commission_log', required=True, string="Commission log",
                                        ondelete="restrict")
    commission_payment_line_id = fields.One2many('oi1_sale_commission_payment_line','commission_payment_log_id', string="Payments")
    log_id = fields.Integer(related="commission_log_id.id")
    name = fields.Char(string="Name", compute="_compute_name")
    partner_id = fields.Many2one(related="commission_log_id.partner_id")
    role_id = fields.Many2one(related="commission_log_id.role_id")
    payment_by = fields.Selection(related="commission_id.payment_by")
    is_sub_commission = fields.Boolean(string="Is a subcommission?", default=False)
    commission_id = fields.Many2one('oi1_commission', required=True, ondelete="restrict", string="Commission")
    payment_move_id  = fields.Many2one('account.move', string="Invoice used for the payment", help="This is the invoice which is used for the payment to the freeworker")

    @api.depends('calculated_rate', 'commission_log_id.name')
    def _compute_name(self):
        for payment_log in self:
            name = ''
            if payment_log.commission_log_id.id:
                name = payment_log.commission_log_id.name
                name += ' ' + _('Source ') + ' '
                name += payment_log.commission_log_id.model_res_id_name
            if payment_log.is_sub_commission and payment_log.commission_id.id:
                name = payment_log.commission_id.name + ' ' + name
            payment_log.name = name

    @api.depends('commission_log_id', 'account_analytic_account_id',
                 'account_analytic_account_id.date', 'is_sub_commission',
                 'commission_id')
    def _compute_calculated_rate(self):
        for commission_payment_log in self:
            if not commission_payment_log.account_analytic_account_id.id:
                continue
            book_date = commission_payment_log.account_analytic_account_id.date
            hour_rate = commission_payment_log.account_analytic_account_id.x_rate
            calculated_rate = 0.0
            if commission_payment_log.commission_payment_line_id.id:
                calculated_rate = commission_payment_log.calculated_rate
            if not commission_payment_log.commission_payment_line_id.id:
                if not commission_payment_log.is_sub_commission:
                    calculated_rate = commission_payment_log.commission_log_id.get_compute_calculation_rate(hour_rate, book_date)
                if commission_payment_log.is_sub_commission:
                    calculated_rate = commission_payment_log.commission_id.get_compute_calculation_rate(
                        hour_rate, book_date)

            if not commission_payment_log.is_sub_commission:
                sub_commissions = self.search([('account_analytic_account_id', '=', commission_payment_log.account_analytic_account_id.id),
                                               ('commission_log_id', '=', commission_payment_log.commission_log_id.id),
                                               ('is_sub_commission', '=', True),
                                               ])
                for sub_commission in sub_commissions:
                    sub_commission._compute_calculated_rate()
                    calculated_rate = calculated_rate - sub_commission.calculated_rate
            commission_payment_log.calculated_rate = calculated_rate

