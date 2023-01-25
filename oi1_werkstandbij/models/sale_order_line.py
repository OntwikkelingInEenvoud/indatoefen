from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_price = fields.Monetary(string="Fee", default=0.0)
    x_surcharge_amount = fields.Float(string="Conversion factor", default=0.0,  digits='Surcharge Amount',)
    x_price_visible = fields.Boolean(string="Price visible", compute="_compute_x_price_visible")
    x_surcharge_amount_visible = fields.Boolean(string="Surcharge amount visible",
                                                compute="_compute_x_surcharge_amount_visible")
    x_poule_id = fields.Many2one('oi1_freeworkerpoule', compute="_compute_x_poule_id", store=True)
    x_basic_hour_rate = fields.Monetary(string="basic hour rate", related="x_poule_id.basichourrate", readonly=False)

    @api.depends('project_id')
    def _compute_x_poule_id(self):
        free_worker_poule_obj = self.env['oi1_freeworkerpoule']
        for sale_order_line in self:
            sale_order_line.x_poule_id = free_worker_poule_obj.get_free_worker_poule(sale_order_line.project_id)

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
        for sol in self:
            surcharge_amount_visible = False
            if sol.x_price == 0.0:
                if sol.x_surcharge_amount != 0.0:
                    surcharge_amount_visible = True
            sol.x_surcharge_amount_visible = surcharge_amount_visible

    """
    2022_0111 Removes the name of the template of the description of the name 
    """
    def _timesheet_create_project(self):
        self.ensure_one()
        project = super()._timesheet_create_project()
        name = self.order_id.name + ' ' + self.order_id.partner_id.name
        project.write({'name': name})
        return project
