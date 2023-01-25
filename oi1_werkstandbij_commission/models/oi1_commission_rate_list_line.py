from odoo import exceptions, models, fields, api, _


class CommissionRateList(models.Model):
    _name = "oi1_commission_rate_list_line"
    _description = "Commission rate list line"

    active = fields.Boolean(string="Active", default=True)
    hour_rate = fields.Monetary(string="Hour rate", default=0.0, help="The hour tariff of the free worker ")
    default_rate = fields.Monetary(string="Rate", default=0.0)
    currency_id = fields.Many2one('res.currency', default=lambda l: l.env.company.currency_id, required=True)
    company_id = fields.Many2one('res.company', default=lambda l: l.env.company, required=True)
    start_date = fields.Date(string="Start date", default=fields.Date.context_today)
    end_date = fields.Date(string="End date")
    rate_list_id = fields.Many2one('oi1_commission_rate_list', string="Rate list", required=True)
    name = fields.Char(string="name", compute="_compute_name", store=True)

    @api.constrains('start_date', 'end_date')
    def _check_end_date_after_start_date(self):
        for rate_list in self:
            if not rate_list.end_date:
                continue
            if rate_list.start_date > rate_list.end_date:
                raise exceptions.UserError(_('An end date  %s should be later than a start date %s of line %s'
                                           % (rate_list.end_date, rate_list.start_date, rate_list.name)))

    @api.depends('rate_list_id', 'rate_list_id.name', 'start_date', 'end_date', 'hour_rate', 'default_rate', 'active')
    def _compute_name(self):
        for rate_list in self:
            name = ''
            if not rate_list.rate_list_id.id:
                continue
            if rate_list.rate_list_id:
                name = rate_list.rate_list_id.name
            if rate_list.start_date:
                name += ' ' + rate_list.start_date.strftime('%d-%m-%Y')
            if rate_list.end_date:
                name += ' ' + rate_list.end_date.strftime('%d-%m-%Y')
            name += str(rate_list.hour_rate)
            name += str(rate_list.default_rate)
            if not rate_list.active:
                name += _(' archived')
            rate_list.name = name.strip()
