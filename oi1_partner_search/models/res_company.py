from odoo import models, fields, api, exceptions,_
import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_partner_search_wildcard = fields.Char (string="Partner search fields",
                                             help="Comma separated field list for searching partners", default="")

    @api.constrains('x_partner_search_wildcard')
    def validate_if_search_wildcard_has_valid_fields(self):
        for company in self:
            if company.x_partner_search_wildcard:
                for field in company.x_partner_search_wildcard.split(","):
                    if field not in self.env['res.partner']._fields:
                        _logger.warning(("The field %s is not within res.partner") % field)

    def write(self, values):
        print(values)
        if 'x_partner_search_wildcard' in values:
            search_code_cron = self.env.ref('oi1_partner_search.calculate_search_code_cron')
            search_code_cron.write({'numbercall': 1, 'active': True})
        return super().write(values)