from odoo import models, fields


class FreeWorker(models.Model):
    _name = 'oi1_insurance_type'
    _description = "Insurance type"

    _sql_constraints = [
        ('oi1_insurance_type_unique_name', 'unique (name)', 'Name already exists')
    ]

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)


