from odoo import models, fields, api, exceptions, _
import logging
from datetime import date

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_poule_id = fields.Many2one('oi1_freeworkerpoule', string="Freeworker poule",
                                 tracking=True,
                                 help="The freeworkers poule which will be used the plan the order")
    x_price = fields.Monetary(string="Fee", default=0.0, tracking=True)
    x_surcharge_amount = fields.Float(string="Conversion factor", default=0.0, tracking=True)
    x_price_visible = fields.Boolean(string="Price visible", compute="_compute_x_price_visible")
    x_surcharge_amount_visible = fields.Boolean(string="Surcharge amount visible",
                                                compute="_compute_x_surcharge_amount_visible")
    x_wsb_ssf_commission_id = fields.Many2one('oi1_commission', string="WSB / SSF afdracht",
                                              help="The payment of funds for making the free workers model and social "
                                                   "entrepreneurship available",
                                              compute="_compute_wsb_ssf_commission_id",
                                              inverse="_set_wsb_ssf_commission_id",
                                              default=lambda self: self._get_default_wsb_ssf_commission(),
                                              store=True)
    x_poule_ids = fields.One2many('oi1_freeworkerpoule', compute="_compute_x_poule_ids", string="Worker poules")
    x_poule_ids_count = fields.Integer(string="Qty Poules", compute="_compute_x_poule_ids_count")
    x_role_wsb_ssf = fields.Many2one('oi1_commission_role', compute="_compute_role_wsb_ssf")
    x_sale_partner_id = fields.Many2one('res.partner', string="Sales partner of the order")


    def _compute_role_wsb_ssf(self):
        for sale_order in self:
            sale_order.x_role_wsb_ssf =  self.env.ref('oi1_werkstandbij.oi1_commission_role_wsb_ssf')

    def do_action_view_free_worker_poule(self):
        action = self.env.ref('oi1_free_worker.freeworkerpoule_order_action').read()[0]
        poules = self.mapped('x_poule_ids')
        if len(poules) > 0:
            action['domain'] = [('id', 'in', poules.ids)]
        else:
            action['domain'] = [('id', '=', -1)]
        return action

    def _compute_x_poule_ids_count(self):
        for so in self:
            so.x_poule_ids_count = len(so.x_poule_ids)

    @api.depends('order_line.x_poule_id')
    def _compute_x_poule_ids(self):
        for so in self:
            so.x_poule_ids = so.mapped('order_line.x_poule_id')

    def _compute_default_x_wsb_ssf_commission_id(self):
        try:
            return self.env.ref('oi1_werkstandbij.oi1_commission_wsb_ssf')
        except Exception as e:
            _logger.error(e)

    @api.constrains('x_price', 'x_surcharge_amount')
    def _validate_x_price_x_surcharge_amount_combination(self):
        not_valid_sales = self.filtered(lambda l: l.x_price != 0.0 and l.x_surcharge_amount != 0.0)
        for not_valid_sale in not_valid_sales:
            raise exceptions.ValidationError(_(" Order %s has a fixed price and a surcharge calculation. "
                                               "This is not possible") % not_valid_sale.name)

    @api.depends('x_price', 'x_surcharge_amount')
    def _compute_x_price_visible(self):
        for so in self:
            price_visible = True
            if so.x_surcharge_amount != 0.0:
                if so.x_price == 0.0:
                    price_visible = False
            so.x_price_visible = price_visible

    @api.depends('x_price', 'x_surcharge_amount')
    def _compute_x_surcharge_amount_visible(self):
        for so in self:
            surcharge_amount_visible = True
            if so.x_price != 0.0:
                if so.x_surcharge_amount == 0.0:
                    surcharge_amount_visible = False
            so.x_surcharge_amount_visible = surcharge_amount_visible

    def name_get(self):
        data = []
        for sale in self:
            display_value = ''
            display_value += sale.name or ""
            display_value += ' '
            display_value += sale.partner_id.name or ""
            if len(sale.client_order_ref or '') > 0:
                display_value += ' ('
                display_value += sale.client_order_ref
                display_value += ')'
            data.append((sale.id, display_value))
        return list(dict.fromkeys(data))

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.search([('name', operator, name)] + args, limit=limit)

        if len(args) == 0:
            Project_obj = self.env['project.project']
            Projects = Project_obj.search([('name', operator, name)], limit=limit)
            for Project in Projects:
                recs += self.search([('x_poule_id', '=', Project.x_poule_id.id)])
            Partner_obj = self.env['res.partner']
            Partners = Partner_obj.search([('name', operator, name)], limit=limit)
            for Partner in Partners:
                recs += self.search([('partner_id', '=', Partner.id)])
        return recs.name_get()

    def _get_default_wsb_ssf_commission(self):
        return self.env.ref('oi1_werkstandbij.oi1_commission_wsb_ssf')

    def _compute_wsb_ssf_commission_id(self):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        oi1_commission_wsb_ssf_role = self.env.ref('oi1_werkstandbij.oi1_commission_role_wsb_ssf')
        model_name = 'sale.order'
        current_date = date.today()
        for sale_order in self:
            x_wsb_ssf_commission_id = oi1_commission_log_obj.get_commission_partner \
                (model_name, sale_order.id, oi1_commission_wsb_ssf_role, current_date)
            if len(x_wsb_ssf_commission_id) == 0:
                x_wsb_ssf_commission_id = self.env.ref('oi1_werkstandbij.oi1_commission_wsb_ssf')
            sale_order.x_wsb_ssf_commission_id = x_wsb_ssf_commission_id

    def _set_wsb_ssf_commission_id(self):
        role_id = self.env.ref('oi1_werkstandbij.oi1_commission_role_wsb_ssf')
        for sale_order in self:
            self._set_sale_order_commission_ids(sale_order.id, sale_order.company_id.partner_id, role_id)
                        
    def set_related_projects_to_active_or_inactive(self, state):
        for sale_order in self:
            project_ids = sale_order.x_poule_id.project_id
            project_ids += sale_order.order_line.project_id
            if state in 'sale':
                project_ids.active = True
            else:
                project_ids.active = False

    def write(self, values):
        res = super().write(values)
        if 'state' in values:
            state = values['state']
            self.set_related_projects_to_active_or_inactive(state)
        return res



