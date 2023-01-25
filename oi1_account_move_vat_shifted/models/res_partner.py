from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_vat_inland_shifted = fields.Boolean(string="Vat inland shifted",
                                          default=False,
                                          help="Choose this option when the BTW can be shifted for "
                                               "inland partners such as within the construction")



