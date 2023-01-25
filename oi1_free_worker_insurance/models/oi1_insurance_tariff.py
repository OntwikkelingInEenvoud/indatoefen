from odoo import models, fields, api, _


class InsuranceTariff(models.Model):
    _name = 'oi1_insurance_tariff'
    _description = "Insurance tariff"

    name = fields.Char(string='Name', compute="_compute_name", store=True)
    active = fields.Boolean(string='Active', default=True, help="This tarif can be used within the insurance polis")
    rate = fields.Monetary(string="Fixed rate", currency_field='currency_id')
    percentage = fields.Float(string="Percentage",
                              help ="The percentage of the hourrate which is paid for the insurance", default=0.00)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id, string="Currency", store=True)
    hour_rate = fields.Monetary(string="Hour rate", currency_field='currency_id',
                                help="The fixed hour rate which is used for the insurance polis", default=0.00)
    partner_id = fields.Many2one('res.partner', string="Vendor", help="The company who is getting the money")
    insurance_id = fields.Many2one('oi1_insurance', string="Insurance polis")

    def calculate_amount(self, hour_line):
        self.ensure_one()
        for insurance_tarif in self:
            amount = insurance_tarif.rate + (hour_line.x_amount * insurance_tarif.percentage/100)
            return amount

    @api.depends('rate','percentage','hour_rate', 'partner_id', 'insurance_id')
    def _compute_name(self):
        for insurance_tariff in self:
            name = ""
            if insurance_tariff.insurance_id.id:
                name = _("insurance") + " " + insurance_tariff.insurance_id.name
            if insurance_tariff.partner_id.id:
                name = name + insurance_tariff.partner_id.name
            if insurance_tariff.hour_rate != 0.0:
                name = name + " " + _("from hour rate") + " " + str(insurance_tariff.hour_rate)
            if insurance_tariff.rate != 0.0:
                name = name + " " + _("fixed rate") + " " + str(insurance_tariff.rate)
            if insurance_tariff.percentage != 0.0:
                name = name + " " + _("percentage") + " " + str(insurance_tariff.percentage)
            insurance_tariff.name = name


