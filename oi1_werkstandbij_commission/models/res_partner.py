from odoo import models, fields, api, _
import logging
from datetime import date

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_oi1_commission_partner_ids = fields.One2many("oi1_commission_partner", 'partner_id', string="Partner Commissions")
    x_account_manager_partner_id = fields.Many2one('res.partner', string="Account manager",
                                                   domain="[('x_is_account_manager', '=', True),]",
                                                   compute="_compute_res_partner_commission_ids",
                                                   inverse="_set_x_account_manager_partner_id",
                                                   store=True, readonly=False,
                                                   )
    x_account_manager_partner_id_amount = fields.Monetary(string="Account manager free",
                                                          compute="_compute_res_partner_commission_ids",
                                                          inverse="_set_x_account_manager_partner_id_amount",
                                                          store=True, readonly=False,
                                                          )

    x_seller_partner_id = fields.Many2one('res.partner', string="Seller",
                                          domain="[('x_is_seller', '=', True),]",
                                          compute="_compute_res_partner_commission_ids",
                                          inverse="_set_x_seller_partner_id",
                                          store=True, readonly=False,
                                          )
    x_seller_partner_id_amount = fields.Monetary(string="Seller free",
                                                 compute="_compute_res_partner_commission_ids",
                                                 inverse="_set_x_seller_partner_id_amount",
                                                 store=True, readonly=False,
                                                 )

    x_is_account_manager = fields.Boolean(string="Is accountmanager", compute="_compute_partner_roles", store=True)
    x_is_mediator = fields.Boolean(string="Is mediator", compute="_compute_partner_roles", store=True)
    x_is_recruiter = fields.Boolean(string="Is recruiter", compute="_compute_partner_roles", store=True)
    x_is_operational_work_planner = fields.Boolean(string="Is workplanner", compute="_compute_partner_roles", store=True)
    x_is_practical_work_planner = fields.Boolean(string="Is practical workplanner",
                                                 compute="_compute_partner_roles", store=True)
    x_is_seller = fields.Boolean(string="Is Seller", compute="_compute_partner_roles", store=True)
    x_is_poule_manager = fields.Boolean(string="Is Poule manager", compute="_compute_partner_roles", store=True)
    x_is_assistant_account_manager = fields.Boolean(string="Is Assistant Account manager",
                                                    compute="_compute_partner_roles", store=True)
    x_commission_period = fields.Selection([('wk', 'Week'), ('mm', 'Month'), ('yy', 'Year'), ('manual', 'Manual')]
                                           , default='wk'
                                           , help="Determines the period of the payments of the commissions"
                                           , string="Commission period"
                                           )
    x_commission_log_ids = fields.One2many('oi1_commission_log', compute="_compute_x_commission_logs_ids")
    x_qty_commission_log_ids = fields.Integer(string="quantity logs", compute="_compute_x_qty_commission_log_ids")

    def do_action_view_commission_logs_on_partner(self):
        action = self.env.ref('oi1_werkstandbij_commission.oi1_commission_log_action').read()[0]
        commission_logs = self.mapped('x_commission_log_ids')
        if len(commission_logs) > 0:
            action['domain'] = [('id', 'in', commission_logs.ids)]
        else:
            action['domain'] = [('id', '=', -1)]
        return action

    def _compute_x_qty_commission_log_ids(self):
        for res_partner in self:
            res_partner.x_qty_commission_log_ids = len(res_partner.x_commission_log_ids)

    def _compute_x_commission_logs_ids(self):
        for res_partner in self:
            oi1_commission_log_obj = self.env['oi1_commission_log']
            res_partner.x_commission_log_ids = oi1_commission_log_obj.search([('res_id', '=', res_partner.id),
                                                                             ('model_name','=', 'res.partner'),
                                                                             ])

    @api.depends('x_oi1_commission_partner_ids', 'x_oi1_commission_partner_ids.commission_id')
    def _compute_partner_roles(self):
        try:
            mediator_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_mediator')
            recruiter_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_recruiter')
            operational_work_planner_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_operational_work_planner')
            practical_work_planner_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_practical_work_planner')
            print(practical_work_planner_role.name);
            account_manager_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_account_manager')
            assistant_account_manager_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_assistant_account_manager')
            seller_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_sales')
            poule_manager_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_poule_manager')
        except Exception as e:
            _logger.warning(e)
            return
        for partner in self:
            partner.x_is_mediator = ResPartner.check_partner_has_role_in_commissions(partner,mediator_role)
            partner.x_is_recruiter = ResPartner.check_partner_has_role_in_commissions(partner,recruiter_role)
            partner.x_is_operational_work_planner = ResPartner.check_partner_has_role_in_commissions(partner, operational_work_planner_role)
            partner.x_is_practical_work_planner = ResPartner.check_partner_has_role_in_commissions(partner, practical_work_planner_role)
            partner.x_is_account_manager = ResPartner.check_partner_has_role_in_commissions(partner, account_manager_role)
            partner.x_is_seller = ResPartner.check_partner_has_role_in_commissions(partner, seller_role)
            partner.x_is_poule_manager = ResPartner.check_partner_has_role_in_commissions(partner, poule_manager_role)
            partner.x_is_assistant_account_manager = ResPartner.check_partner_has_role_in_commissions(partner, assistant_account_manager_role)

    @staticmethod
    def get_default_commission_tariff(partner, commission_role_id, commission_id=False):
        commission_tariffs = partner.x_oi1_commission_partner_ids. \
            filtered(lambda l: l.commission_id.commission_role_id.id == commission_role_id.id)
        if len(commission_tariffs) == 0:
            if not commission_id:
                return 0.0
            return commission_id.default_rate
        return commission_tariffs[0].calculation_rate

    @staticmethod
    def check_partner_has_role_in_commissions(partner, commission_role_id):
        has_role_in_commissions = partner.x_oi1_commission_partner_ids.\
                filtered(lambda l:l.commission_id.commission_role_id.id == commission_role_id.id)
        if len(has_role_in_commissions) > 0:
            return True
        return False

    @api.model
    def get_commission_period(self, partner, date):
        period = partner.x_commission_period
        if period == 'wk':
            return _("Week ") + str(date.year) + ("0" + str(date.strftime('%V')))[-2:]
        if period == 'mm':
            return _("Month ") + str(date.year) + ("0" + str(date.month))[-2:]
        if period == 'yy':
            return _("Year ") + str(date.year)
        return _("Manual")

    def _compute_res_partner_commission_ids(self):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        oi1_commission_role_obj = self.env['oi1_commission_role']
        model_name = 'res.partner'
        current_date = date.today()

        for res_partner in self:
            commission_x_seller_partner_id = oi1_commission_log_obj.get_commission_partner \
                (model_name, res_partner.id, oi1_commission_role_obj.get_seller_role(), current_date)
            commission_x_account_manager_partner_id = oi1_commission_log_obj.get_commission_partner \
                (model_name, res_partner.id, oi1_commission_role_obj.get_account_manager_role(), current_date)

            res_partner.x_seller_partner_id = commission_x_seller_partner_id.partner_id
            res_partner.x_seller_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(commission_x_seller_partner_id)

            res_partner.x_account_manager_partner_id = commission_x_account_manager_partner_id.partner_id
            res_partner.x_account_manager_partner_id_amount = oi1_commission_log_obj.get_fee_amount_from_commission_log(commission_x_account_manager_partner_id)

    def _set_x_account_manager_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_account_manager_role()
        for res_partner in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(
                res_partner.x_account_manager_partner_id, role_id)
            oi1_commission_log = self._set_res_partner_commission_ids(res_partner.id, res_partner.x_account_manager_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                res_partner.x_account_manager_partner_id_amount = oi1_commission_log.default_rate

    def _set_x_account_manager_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_account_manager_role()
        for res_partner in self:
            self._set_res_partner_commission_ids(res_partner.id,
                                                 res_partner.x_account_manager_partner_id,
                                                 role_id,
                                                 res_partner.x_account_manager_partner_id_amount)

    def _set_x_seller_partner_id(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_seller_role()
        for res_partner in self:
            default_tariff = self.env['res.partner'].get_default_commission_tariff(
                res_partner.x_seller_partner_id, role_id)
            oi1_commission_log = self._set_res_partner_commission_ids(res_partner.id, res_partner.x_seller_partner_id, role_id, default_tariff)
            if oi1_commission_log:
                res_partner.x_seller_partner_id_amount = oi1_commission_log.default_rate

    def _set_x_seller_partner_id_amount(self):
        oi1_commission_role_obj = self.env['oi1_commission_role']
        role_id = oi1_commission_role_obj.get_seller_role()
        for res_partner in self:
            oi1_commission_log = self._set_res_partner_commission_ids(res_partner.id,
                                                 res_partner.x_seller_partner_id,
                                                 role_id,
                                                 res_partner.x_seller_partner_id_amount)
            return oi1_commission_log

    @api.model
    def _set_res_partner_commission_ids(self, res_id, partner_id, role_id, default_tariff):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        model_name = 'res.partner'
        current_date = date.today()
        return oi1_commission_log_obj.set_commission_log(
            model_name, res_id, partner_id,
            role_id, current_date,
            False, default_tariff)