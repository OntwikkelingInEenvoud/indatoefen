from odoo import models, fields


class Insurance(models.Model):
    _name = 'oi1_insurance'
    _description = "Insurance"

    _sql_constraints = [
        ('oi1_insurance_unique_name', 'unique (name)', 'Name already exists')
    ]

    name = fields.Char(string='Name', required=True, translate=True, help="The description of the insurance")
    partner_id = fields.Many2one('res.partner', string="Insurance company", help="The default insurance company")
    insurance_type_id = fields.Many2one('oi1_insurance_type', string="Type", help="The general type of the insurance",
                                        required=True)
    duration = fields.Integer(string="Duration", help="Duration in days for no end date provide -1")
    active = fields.Boolean(string="Active", default=True)
    commission_id = fields.Many2one('oi1_commission', string="Commission",
                                    help="The commission which is used for the payment of the free worker")
    insurance_tariff_ids = fields.One2many('oi1_insurance_tariff', 'insurance_id', string="Tariffs")
    insturance_ids = fields.Many2many('oi1_insurance_package', 'oi1_package_oi1_insurane_rel', 'insurance_id', 'package_id')

    def calculate_amount(self,  hour_line):
        self.ensure_one()
        amount = 0.0
        for insurance_tarif in self.insurance_tariff_ids:
            amount += insurance_tarif.calculate_amount(hour_line)
        return amount



