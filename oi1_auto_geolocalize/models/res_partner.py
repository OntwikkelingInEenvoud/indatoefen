# -*- coding: utf-8 -*-

from odoo import models, api
import logging
import datetime

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def cron_geo_localize(self):
        partner_obj = self.env['res.partner']
        partners = partner_obj.search([], order="write_date desc")
        partners = partners.filtered(lambda l: not l.parent_id.id or l.type != 'contact')
        partners = partners.filtered(lambda l: not l.date_localization or l.date_localization < l.write_date.date())
        partners = partners.filtered(lambda l: not l.date_localization or l.date_localization < datetime.date.today() - datetime.timedelta(days=10))
        
        if len(partners) > 25:
            partners = partners[0:25]
        for partner in partners:
            try:
                _logger.debug("Geo localization partner %s" % partner.name)
                partner.geo_localize()
                partner.date_localization = partner.write_date
            except:
                _logger.warning("Failure geo locating partner %s" % partner.name)

