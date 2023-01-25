from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_insurance_package_id = fields.Many2one('oi1_insurance_package', string="Insurance Package", tracking=True)

    @api.onchange
    def on_change_partner_id_insurance_package_id(self):
        for so in self:
            so.x_insurance_package_id = so.partner_id.x_insurance_default_package_id
