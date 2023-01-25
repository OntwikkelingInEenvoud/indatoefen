
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_insurance_default_package_id = fields.Many2one('oi1_insurance_package',
                                                     string="Default insurance Package",
                                                     help="Default package for sales orders")