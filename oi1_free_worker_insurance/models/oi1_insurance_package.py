from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InsurancePackage(models.Model):
    _name = 'oi1_insurance_package'
    _description = "Insurance package"

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string="Name", compute="_compute_name", store=True)
    description = fields.Char(string="Description", required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    insurance_ids = fields.Many2many('oi1_insurance', 'oi1_package_oi1_insurane_rel', 'package_id', 'insurance_id')
    default_free_worker = fields.Boolean(string="Default for free worker", help="This package automatically linked when a free worker is created")

    @api.constrains('default_free_worker')
    def _only_1_package_is_default_free_worker(self):
        for package in self:
            if package.default_free_worker:
                packages = self.search([('default_free_worker', '=', True),('id','!=', package.id)])
                if len(packages) > 0:
                    raise ValidationError(_('The package  %s is already set as default.') % packages[0])

    @api.depends('code', 'description')
    def _compute_name(self):
        for package in self:
            name = ""
            if package.code:
                name = name + package.code
            if package.description:
                name = name + ' ' + package.description
            package.name = name.strip()

    def calculate_amount(self,  hour_line):
        self.ensure_one()
        amount = 0.0
        for insurance in self.insurance_ids:
            amount += insurance.calculate_amount(hour_line)
        return amount


