from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def name_get(self):
        data = []
        for project in self:
            display_value = ''
            display_value += project.name or ""
            if project.sale_order_id.id:
                display_value += ' (' + project.sale_order_id.name + ' , ' + project.sale_order_id.partner_id.name + ')'
            data.append((project.id, display_value))
        return list(dict.fromkeys(data))

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.search(['|', '|', ('name', operator, name), ('sale_order_id.partner_id.name', operator, name),('sale_order_id.name', operator, name)] + args, limit=limit)
        return recs.name_get()