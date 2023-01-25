from odoo import models, fields, api
from datetime import date


class FreeWorker(models.Model):
    _inherit = 'oi1_free_worker'

    mediator_partner_id = fields.Many2one('res.partner', string="Mediator", help="Who is the mediator of the freeworker",
                                          domain="[('x_is_mediator', '=', True),]",
                                          compute="_compute_free_worker_commission_ids",
                                          inverse="_set_mediator_partner_id",
                                          store=True, readonly=False,
                                          )
    mediator_partner_id_amount = fields.Monetary(string="Mediator fee", default=0.0,
                                                 compute="_compute_free_worker_commission_ids",
                                                 inverse="_set_mediator_partner_id_amount",
                                                 store=True, readonly=False)

    recruiter_partner_id = fields.Many2one('res.partner', string="Recruiter", domain=([('x_is_recruiter', '=', True)]),
                                           help="Who has recruited the free worker",
                                           compute="_compute_free_worker_commission_ids",
                                           inverse="_set_recruiter_partner_id",
                                           store=True, readonly=False,
                                            )
    recruiter_partner_id_amount = fields.Monetary(string="Recruiter fee", default=0.0,
                                                  compute="_compute_free_worker_commission_ids",
                                                  inverse="_set_recruiter_partner_id_amount",
                                                  store=True, readonly=False
                                                  )

    practical_work_planner_partner_id = fields.Many2one('res.partner', string="Practical work planner",
                                                         domain=([('x_is_practical_work_planner', '=', True)]),
                                           help="Who is responsible for the daily support of the freeworker",
                                           compute="_compute_free_worker_commission_ids",
                                           inverse="_set_practical_work_planner_partner_id",
                                           store=True, readonly=False,
                                           )
    practical_work_planner_partner_id_amount = fields.Monetary(string="Practical work planner fee", default=0.0,
                                                               compute="_compute_free_worker_commission_ids",
                                                               inverse="_set_practical_work_planner_partner_id_amount",
                                                               store=True, readonly=False)

    commission_free_worker_ids = fields.One2many('oi1_commission_free_worker', 'free_worker_id')

    commission_log_ids = fields.One2many('oi1_commission_log', compute="_compute_x_commission_logs_ids")
    qty_commission_log_ids = fields.Integer(string="freeworker quantity logs", compute="_compute_x_qty_commission_log_ids")

    def do_action_view_commission_logs_on_free_worker(self):
        action = self.env.ref('oi1_werkstandbij_commission.oi1_commission_log_action').read()[0]
        commission_logs = self.mapped('commission_log_ids')
        if len(commission_logs) > 0:
            action['domain'] = [('id', 'in', commission_logs.ids)]
        else:
            action['domain'] = [('id', '=', -1)]
        return action

    def _compute_x_qty_commission_log_ids(self):
        for free_worker in self:
            free_worker.qty_commission_log_ids = len(free_worker.commission_log_ids)

    @api.depends('practical_work_planner_partner_id', 'recruiter_partner_id', 'mediator_partner_id')
    def _compute_x_commission_logs_ids(self):
        for free_worker in self:
            oi1_commission_log_obj = self.env['oi1_commission_log']
            free_worker.commission_log_ids = oi1_commission_log_obj.search([('res_id', '=', free_worker.id),
                                                                              ('model_name', '=', 'oi1_free_worker'),
                                                                              ])
    def _set_mediator_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_mediator_role()
        for free_worker in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(
                free_worker.mediator_partner_id, role_id)
            oi1_commission_log = self._set_free_worker_commission_ids(free_worker.id, free_worker.mediator_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                free_worker.mediator_partner_id_amount = oi1_commission_log.default_rate

    def _set_mediator_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_mediator_role()
        for free_worker in self:
            self._set_free_worker_commission_ids(free_worker.id,
                                                 free_worker.mediator_partner_id,
                                                 role_id,
                                                 free_worker.mediator_partner_id_amount)

    def _set_recruiter_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_recruiter_role()
        for free_worker in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(
                free_worker.recruiter_partner_id, role_id)
            oi1_commission_log = self._set_free_worker_commission_ids(free_worker.id, free_worker.recruiter_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                free_worker.recruiter_partner_id_amount = oi1_commission_log.default_rate

    def _set_recruiter_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_recruiter_role()
        for free_worker in self:
            self._set_free_worker_commission_ids(free_worker.id,
                                                 free_worker.recruiter_partner_id,
                                                 role_id,
                                                 free_worker.recruiter_partner_id_amount)

    def _set_practical_work_planner_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_practical_work_planner_role()
        for free_worker in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(
                free_worker.practical_work_planner_partner_id, role_id)
            oi1_commission_log = self._set_free_worker_commission_ids(free_worker.id, free_worker.practical_work_planner_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                free_worker.practical_work_planner_partner_id_amount = oi1_commission_log.default_rate

    def _set_practical_work_planner_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_practical_work_planner_role()
        for free_worker in self:
            self._set_free_worker_commission_ids(free_worker.id,
                                                 free_worker.practical_work_planner_partner_id,
                                                 role_id,
                                                 free_worker.practical_work_planner_partner_id_amount)

    @api.model
    def _set_free_worker_commission_ids(self, res_id, partner_id, role_id, default_tariff=False):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        model_name = 'oi1_free_worker'
        current_date = date.today()
        return oi1_commission_log_obj.set_commission_log(
            model_name, res_id, partner_id,
            role_id, current_date,
            False, default_tariff)

    def _compute_free_worker_commission_ids(self):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        oi1_commission_role_obj = self.env['oi1_commission_role']
        model_name = 'oi1_free_worker'
        current_date = date.today()

        for free_worker in self:
            commission_mediator_partner_id = oi1_commission_log_obj.get_commission_partner \
                (model_name, free_worker.id, oi1_commission_role_obj.get_mediator_role(), current_date)
            commission_recruiter_partner_id = oi1_commission_log_obj.get_commission_partner \
                (model_name, free_worker.id, oi1_commission_role_obj.get_recruiter_role(), current_date)
            commission_practical_work_planner_partner_id = oi1_commission_log_obj.get_commission_partner \
                (model_name, free_worker.id, oi1_commission_role_obj.get_practical_work_planner_role(), current_date)

            free_worker.mediator_partner_id = commission_mediator_partner_id.partner_id

            free_worker.mediator_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(
                commission_mediator_partner_id)

            free_worker.recruiter_partner_id = commission_recruiter_partner_id.partner_id
            free_worker.recruiter_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(
                commission_recruiter_partner_id)

            free_worker.practical_work_planner_partner_id = commission_practical_work_planner_partner_id.partner_id
            free_worker.practical_work_planner_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(
                commission_practical_work_planner_partner_id)



