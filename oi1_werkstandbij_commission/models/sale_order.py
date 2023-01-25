from odoo import models, fields, api
from datetime import date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_seller_partner_id = fields.Many2one('res.partner', string="Seller",
                                          domain="[('x_is_seller', '=', True),]",
                                          compute="_compute_sale_order_commission_ids",
                                          inverse="_set_x_seller_partner_id",
                                          store=True, readonly=False)

    x_seller_partner_id_amount = fields.Monetary(string="Seller free",
                                                 compute="_compute_sale_order_commission_ids",
                                                 inverse="_set_seller_partner_id_amount",
                                                 store=True, readonly=False,
                                                 default=0.0)

    x_account_manager_partner_id = fields.Many2one('res.partner', string="Account manager",
                                                   domain="[('x_is_account_manager', '=', True),]",
                                                   compute="_compute_sale_order_commission_ids", store=True,
                                                   inverse="_set_x_account_manager_partner_id", readonly=False
                                                   )

    x_account_manager_partner_id_amount = fields.Monetary(string="Account manager free",
                                                          compute="_compute_sale_order_commission_ids",
                                                          inverse="_set_x_account_manager_partner_id_amount",
                                                          store=True, readonly=False,
                                                          default=0.0)

    x_assistant_account_manager_partner_id = fields.Many2one('res.partner', string="As. Account manager",
                                                   domain="[('x_is_assistant_account_manager', '=', True),]",
                                                   compute="_compute_sale_order_commission_ids", store=True,
                                                   inverse="_set_x_assistant_account_manager_partner_id", readonly=False
                                                   )
    x_assistant_account_manager_partner_id_amount = fields.Monetary(string="Account manager assistant free",
                                                                    compute="_compute_sale_order_commission_ids",
                                                                    inverse="_set_x_assistant_account_manager_partner_id_amount",
                                                                    store=True, readonly=False,
                                                                    default=0.0)

    x_reservation_amount = fields.Monetary(string="Reservation Amount",
                                           compute="_compute_sale_order_commission_ids",
                                           inverse="_set_x_reservation_amount", store=True,
                                           readonly=False
                                           )

    x_commission_log_ids = fields.One2many('oi1_commission_log', compute="_compute_x_commission_logs_ids")
    x_qty_commission_log_ids = fields.Integer(string="quantity logs", compute="_compute_x_qty_commission_log_ids")

    def _compute_x_qty_commission_log_ids(self):
        for sale_order in self:
            sale_order.x_qty_commission_log_ids = len(sale_order.x_commission_log_ids)

    def do_action_view_commission_logs_on_order(self):
        action = self.env.ref('oi1_werkstandbij_commission.oi1_commission_log_action').read()[0]
        commission_logs = self.mapped('x_commission_log_ids')
        if len(commission_logs) > 0:
            action['domain'] = [('id', 'in', commission_logs.ids)]
        else:
            action['domain'] = [('id', '=', -1)]
        return action

    @api.depends('x_seller_partner_id', 'x_account_manager_partner_id', 'x_assistant_account_manager_partner_id')
    def _compute_x_commission_logs_ids(self):
        for sale_order in self:
            oi1_commission_log_obj = self.env['oi1_commission_log']
            sale_order.x_commission_log_ids = oi1_commission_log_obj.search([('res_id', '=', sale_order.id),
                                                                             ('model_name','=', 'sale.order'),
                                                                             ])

    def _set_x_reservation_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_reservation_role()
        for sale_order in self:
            self._set_sale_order_commission_ids(sale_order.id,
                                                self.env.company.partner_id,
                                                role_id,
                                                sale_order.x_reservation_amount)

    def _set_x_account_manager_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_account_manager_role()
        for sale_order in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(sale_order.x_account_manager_partner_id, role_id)
            oi1_commission_log = self._set_sale_order_commission_ids(sale_order.id, sale_order.x_account_manager_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                sale_order.x_account_manager_partner_id_amount = oi1_commission_log.default_rate

    def _set_x_account_manager_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_account_manager_role()
        for sale_order in self:
            self._set_sale_order_commission_ids(sale_order.id,
                                                sale_order.x_account_manager_partner_id,
                                                role_id,
                                                sale_order.x_account_manager_partner_id_amount)

    def _set_x_assistant_account_manager_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_assistant_account_manager_role()
        for sale_order in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(sale_order.x_assistant_account_manager_partner_id, role_id)
            oi1_commission_log  = self._set_sale_order_commission_ids(sale_order.id, sale_order.x_assistant_account_manager_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                sale_order.x_assistant_account_manager_partner_id_amount = oi1_commission_log.default_rate

    def _set_x_assistant_account_manager_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_assistant_account_manager_role()
        for sale_order in self:
            self.env['res.partner'].get_default_commission_tariff(sale_order.x_assistant_account_manager_partner_id,
                                                                                   role_id)
            self._set_sale_order_commission_ids(sale_order.id,
                                                sale_order.x_assistant_account_manager_partner_id,
                                                role_id,
                                                sale_order.x_assistant_account_manager_partner_id_amount)

    def _set_x_seller_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_seller_role()
        for sale_order in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(sale_order.x_seller_partner_id, role_id)
            oi1_commission_log = self._set_sale_order_commission_ids(sale_order.id, sale_order.x_seller_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                sale_order.x_seller_partner_id_amount = oi1_commission_log.default_rate

    def _set_seller_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_seller_role()
        for sale_order in self:
            self._set_sale_order_commission_ids(sale_order.id,
                                                sale_order.x_seller_partner_id,
                                                role_id,
                                                sale_order.x_seller_partner_id_amount)

    @api.model
    def _set_sale_order_commission_ids(self, res_id, partner_id, role_id, default_rate=False):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        model_name = 'sale.order'
        current_date = date.today()
        return oi1_commission_log_obj.set_commission_log(
            model_name, res_id, partner_id,
            role_id, current_date,
            False, default_rate)

    def _compute_sale_order_commission_ids(self):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        oi1_commission_role_obj = self.env['oi1_commission_role']
        model_name = 'sale.order'
        current_date = date.today()

        for sale_order in self:
            commission_seller_partner = oi1_commission_log_obj.get_commission_partner \
                (model_name, sale_order.id, oi1_commission_role_obj.get_seller_role(), current_date)
            commission_account_manager_partner = oi1_commission_log_obj.get_commission_partner \
                (model_name, sale_order.id, oi1_commission_role_obj.get_account_manager_role(), current_date)
            commission_assistant_account_manager_partner = oi1_commission_log_obj.get_commission_partner \
                (model_name, sale_order.id, oi1_commission_role_obj.get_assistant_account_manager_role(), current_date)
            commission_reservation = oi1_commission_log_obj.get_commission_partner \
                (model_name, sale_order.id, oi1_commission_role_obj.get_reservation_role(), current_date)

            sale_order.x_seller_partner_id = commission_seller_partner.partner_id
            sale_order.x_seller_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(commission_seller_partner)

            sale_order.x_account_manager_partner_id = commission_account_manager_partner.partner_id
            sale_order.x_account_manager_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(commission_account_manager_partner)

            sale_order.x_assistant_account_manager_partner_id = commission_assistant_account_manager_partner.partner_id
            sale_order.x_assistant_account_manager_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(commission_assistant_account_manager_partner)

            sale_order.x_reservation_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(commission_reservation)