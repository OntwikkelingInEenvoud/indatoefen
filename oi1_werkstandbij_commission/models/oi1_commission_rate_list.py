from odoo import models, fields, api


class CommissionRateList(models.Model):
    _name = "oi1_commission_rate_list"
    _description = "Commission rate list"

    name = fields.Char(string="Name", required=True, help="The name of the commission rate list")
    active = fields.Boolean(string="Active", default=True)
    rate_list_line_ids = fields.One2many('oi1_commission_rate_list_line', 'rate_list_id', string="Rate list lines")
    company_id = fields.Many2one('res.company', string="Company", default=lambda l: l.env.company)

    def get_tariff_with_given_hour_rate(self, hour_rate, book_date):
        self.ensure_one()
        default_rate = 0.0
        oi1_commission_rate_list_line_obj = self.env['oi1_commission_rate_list_line']
        oi1_commission_rate_list_line = oi1_commission_rate_list_line_obj.search([('rate_list_id', '=', self.id),
                                                                                  ('start_date','<=', book_date),
                                                                                  '|', ('end_date', '>', book_date), ('end_date','=', False),
                                                                                  ('hour_rate', '<=', hour_rate),
                                                                                  ], order='hour_rate desc', limit=1)
        if len(oi1_commission_rate_list_line) > 0:
            default_rate = oi1_commission_rate_list_line.default_rate
        return default_rate