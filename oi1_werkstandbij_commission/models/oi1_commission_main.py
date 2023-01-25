from odoo import api, models, fields, exceptions, _


class Commission(models.Model):
    _name = "oi1_commission_main"
    _description = "Commission"

    partner_id = fields.Many2one('res.partner', required=True)
    commission_id = fields.Many2one('oi1_commission', required=True, help="The commission related to the role")
    use_default_rate = fields.Boolean(string="Use default rate", default=True,
                                      help="Determines if the partner uses the default commission rate or decides to have his own rate")
    default_rate = fields.Monetary(string="Default rate",
                                   help="The rate the partners wants to earn for the role")
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company,
                                 help="Company related to this commission")
    calculation_rate = fields.Monetary(string="Calculation rate", compute="_compute_calculation_rate")
    name = fields.Char(string="Name", compute="_compute_name")
    active = fields.Boolean(string="Active", default=True)
    commission_rate_list_id = fields.Many2one('oi1_commission_rate_list', string="Rates")
    commission_role_id = fields.Many2one(related="commission_id.commission_role_id")

    def get_compute_calculation_rate(self, hour_rate, book_date):
        self.ensure_one()
        if self.use_default_rate:
            if self.commission_id:
                return self.commission_id.get_compute_calculation_rate(hour_rate, book_date)
            else:
                return 0.0
        if self.commission_rate_list_id.id:
            return self.commission_rate_list_id.get_tariff_with_given_hour_rate(hour_rate, book_date)
        return self.default_rate

    @api.depends('partner_id.name', 'commission_id.name')
    def _compute_name(self):
        for commission in self:
            commission.name = commission.partner_id.name + ' ' + commission.commission_id.name

    @api.depends('commission_id.sub_commission_ids', 'commission_id.sub_commission_ids.default_rate')
    def _compute_calculation_rate(self):
        for commission_main in self:
            calculation_rate = commission_main.default_rate
            for sub_commission in commission_main.commission_id.sub_commission_ids:
                calculation_rate = calculation_rate - sub_commission.default_rate
            if calculation_rate < 0.0:
                raise exceptions.UserError(
                    _("Check the commission %s because the amount of the subcommissions is higher then the commission amount ") % commission_main.name)
            commission_main.calculation_rate = calculation_rate

    def create(self, values):
        commission_main = super().create(values)
        if isinstance(values, list):
            values = values[0]
        commission_main.write_default_to_commission_main(values)
        return commission_main

    def write(self, values):
        if values.get('use_default_rate', False):
            self.write_default_to_commission_main(values)
        return super().write(values)

    def write_default_to_commission_main(self, values):
        for commission_main in self:
            commission_id = values.get('commission_id', commission_main.commission_id.id)
            default_rate = self.env['oi1_commission'].browse([commission_id]).default_rate
            commission_main.write({'default_rate': default_rate})
