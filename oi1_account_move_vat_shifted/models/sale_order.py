from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_vat_inland_shifted = fields.Boolean(string="Vat inland shifted", default=False,
                                          help="Choose this option when the BTW can be shifted for "
                                               "inland partners such as within the construction")

    @api.onchange('partner_id')
    def determine_vat_inland_shifted_from_partner_id(self):
        for sale_order in self:
            if sale_order.partner_id.id:
                sale_order.x_vat_inland_shifted = sale_order.partner_id.x_vat_inland_shifted
            else:
                sale_order.x_vat_inland_shifted = False
