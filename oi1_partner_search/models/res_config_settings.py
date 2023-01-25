from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_partner_search_wildcard = fields.Char(related="company_id.x_partner_search_wildcard", readonly=False)


