from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_search_string = fields.Char(string="Search")

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        return super().search(args, offset, limit, order, count)

    def write(self, values):
        res = super().write(values)
        if res:
            self.calculate_search(values)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.calculate_search(vals_list)
        return res

    def calculate_search(self, values):
        for partner in self:
            search_string = partner.display_name
            for field in self.get_search_fields(partner).split(","):
                value = partner.mapped(field)
                if len(value) > 0:
                    value = value[0]
                    if value:
                        search_string = search_string + str(value)
            if search_string != partner.x_search_string:
                partner.write({'x_search_string': search_string})

    @api.model
    def get_search_fields(self, partner_id):
        company_obj = self.env['res.company']
        search_fields = ''
        if partner_id.sudo().company_id.x_partner_search_wildcard:
            search_fields = partner_id.sudo().company_id.x_partner_search_wildcard
        if len(search_fields) == 0:
            companies = company_obj.sudo().search([('x_partner_search_wildcard', '!=', False)], order="id")
            if len(companies) > 0:
                search_fields = companies[0].sudo().x_partner_search_wildcard
        return search_fields

    @api.model
    def do_calculate_search_code_cron(self):
        partners = self.search([])
        values = {}
        partners.calculate_search(values)
