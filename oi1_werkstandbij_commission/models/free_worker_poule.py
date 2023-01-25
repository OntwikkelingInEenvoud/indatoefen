from odoo import models, fields, api
from datetime import date


class FreeWorkerPoule(models.Model):
    _inherit = "oi1_freeworkerpoule"

    poule_manager_partner_id = fields.Many2one('res.partner', string="Poule manager",
                                               domain="[('x_is_poule_manager', '=', True)]",
                                               compute="_compute_free_worker_poule_commission_ids",
                                               inverse="_set_poule_manager_partner_id",
                                               store=True, readonly=False,
                                               help="The person who makes sure that there are enough free workers within the poule and that they work well together"
                                               )
    poule_manager_partner_id_amount = fields.Monetary(string="Poule manager free", default=0.0,
                                                      compute="_compute_free_worker_poule_commission_ids",
                                                      inverse="_set_poule_manager_partner_id_amount",
                                                      store=True, readonly=False
                                                      )

    operational_work_planner_partner_id = fields.Many2one('res.partner', string="Operational work planner",
                                                          domain="[('x_is_operational_work_planner', '=', True)]",
                                                          compute="_compute_free_worker_poule_commission_ids",
                                                          inverse="_set_operational_work_planner_partner_id",
                                                          store=True, readonly=False,
                                                          help="The person who helps the free worker with the daily tasks within the poule"
                                                          )
    operational_work_planner_partner_id_amount = fields.Monetary(string="Operational workplanner free", default=0.0,
                                                                 compute="_compute_free_worker_poule_commission_ids",
                                                                 inverse="_set_operational_work_planner_partner_id_amount",
                                                                 store=True, readonly=False
                                                                 )

    reservation_amount = fields.Monetary(string="Reservation Amount", default=0.0,
                                           compute="_compute_free_worker_poule_commission_ids",
                                           inverse="_set_reservation_amount",
                                           readonly=False, store=True
                                           )

    commission_log_ids = fields.One2many('oi1_commission_log', compute="_compute_x_commission_logs_ids")
    qty_commission_log_ids = fields.Integer(string="quantity logs", compute="_compute_x_qty_commission_log_ids")

    def do_action_view_commission_logs_on_free_worker_poule(self):
        action = self.env.ref('oi1_werkstandbij_commission.oi1_commission_log_action').read()[0]
        commission_logs = self.mapped('commission_log_ids')
        if len(commission_logs) > 0:
            action['domain'] = [('id', 'in', commission_logs.ids)]
        else:
            action['domain'] = [('id', '=', -1)]
        return action

    def _set_reservation_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_reservation_role()
        for free_worker_poule in self:
            self._set_free_worker_poule_commission_ids \
                (free_worker_poule.id, self.env.company.partner_id, role_id, free_worker_poule.reservation_amount)

    def _compute_x_qty_commission_log_ids(self):
        for free_worker_poule in self:
            free_worker_poule.qty_commission_log_ids = len(free_worker_poule.commission_log_ids)

    def _compute_x_commission_logs_ids(self):
        for free_worker_poule in self:
            oi1_commission_log_obj = self.env['oi1_commission_log']
            free_worker_poule.commission_log_ids = oi1_commission_log_obj.search([('res_id', '=', free_worker_poule.id),
                                                                             ('model_name', '=', 'oi1_freeworkerpoule'),
                                                                             ])

    def _set_operational_work_planner_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_operational_work_planner_role()
        for free_worker_poule in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(
                free_worker_poule.operational_work_planner_partner_id, role_id)
            oi1_commission_log = self._set_free_worker_poule_commission_ids\
                (free_worker_poule.id, free_worker_poule.operational_work_planner_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                free_worker_poule.operational_work_planner_partner_id_amount = oi1_commission_log.default_rate

    def _set_operational_work_planner_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_operational_work_planner_role()
        for free_worker_poule in self:
            self._set_free_worker_poule_commission_ids \
                (free_worker_poule.id,
                 free_worker_poule.operational_work_planner_partner_id,
                 role_id,
                 free_worker_poule.operational_work_planner_partner_id_amount)

    def _set_poule_manager_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_poule_manager_role()
        for free_worker_poule in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(
                free_worker_poule.poule_manager_partner_id, role_id)
            oi1_commission_log = self._set_free_worker_poule_commission_ids\
                (free_worker_poule.id, free_worker_poule.poule_manager_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                free_worker_poule.poule_manager_partner_id_amount = oi1_commission_log.default_rate

    def _set_poule_manager_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_poule_manager_role()
        for free_worker_poule in self:
            self._set_free_worker_poule_commission_ids\
                (free_worker_poule.id,
                 free_worker_poule.poule_manager_partner_id,
                 role_id,
                 free_worker_poule.poule_manager_partner_id_amount)

    @api.model
    def _set_free_worker_poule_commission_ids(self, res_id, partner_id, role_id, default_tariff):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        model_name = 'oi1_freeworkerpoule'
        current_date = date.today()
        return oi1_commission_log_obj.set_commission_log(
            model_name, res_id, partner_id,
            role_id, current_date,
            False, default_tariff)

    def _compute_free_worker_poule_commission_ids(self):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        oi1_commission_role_obj = self.env['oi1_commission_role']
        model_name = 'oi1_freeworkerpoule'
        current_date = date.today()

        for free_worker_poule in self:
            commission_poule_manager = oi1_commission_log_obj.get_commission_partner \
                (model_name, free_worker_poule.id, oi1_commission_role_obj.get_poule_manager_role(), current_date)
            commission_poule_operational_work_planner = oi1_commission_log_obj.get_commission_partner \
                (model_name, free_worker_poule.id, oi1_commission_role_obj.get_operational_work_planner_role(), current_date)
            commission_reservation = oi1_commission_log_obj.get_commission_partner \
                (model_name, free_worker_poule.id, oi1_commission_role_obj.get_reservation_role(), current_date)

            free_worker_poule.poule_manager_partner_id = commission_poule_manager.partner_id
            free_worker_poule.poule_manager_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(commission_poule_manager)
            free_worker_poule.operational_work_planner_partner_id = commission_poule_operational_work_planner.partner_id
            free_worker_poule.operational_work_planner_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(commission_poule_operational_work_planner)

            free_worker_poule.reservation_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(
                commission_reservation)



