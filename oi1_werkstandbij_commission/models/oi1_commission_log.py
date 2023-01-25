from odoo import api, models, fields, exceptions, _
import datetime
import logging

_logger = logging.getLogger(__name__)


class CommissionLog(models.Model):
    _name = "oi1_commission_log"
    _description = "Commission log"
    _order = 'start_date asc,end_date asc'

    _sql_constraints = [
        ('modelname_res_id_commission_id_start_date_unique', 'unique (model_name, res_id, commission_id, start_date)',
         'The combination of model_name, res_id, role_id and start_date should be unique'),
    ]

    model_name = fields.Char(string="Model")
    res_id = fields.Integer(string="Id")
    partner_id = fields.Many2one('res.partner', string="Partner", required=True, ondelete='restrict')
    role_id = fields.Many2one('oi1_commission_role', string="Commission role", required=True, ondelete='restrict')
    start_date = fields.Date(string="Start date")
    end_date = fields.Date(string="End date")
    default_rate = fields.Monetary(string="Default rate",
                                   help="The rate the partners wants to earn for the role", default=0.0)
    use_default = fields.Boolean(string="Use default", default=True)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id, ondelete='restrict')
    is_actual = fields.Boolean(string="Actual", compute="_compute_is_actual")
    commission_main_id = fields.Many2one('oi1_commission_main', string="Related commission",
                                         compute="_compute_commission_main_id", store=True, ondelete='restrict')
    commission_id = fields.Many2one('oi1_commission', string="Commission", ondelete='restrict', required=True)
    commission_rate_list_id = fields.Many2one('oi1_commission_rate_list', string="Commission rate", ondelete='restrict')
    name = fields.Char(string="Name", compute="_compute_name", store=True)
    payment_by = fields.Char(string="Payment by", compute="_compute_payment_by")
    model_res_id_name = fields.Char(string="Model name", compute="_compute_model_res_id_name",
                                    help="Shows the person on which the log is created")
    commission_free_worker_id = fields.Many2one('oi1_commission_free_worker')
    model_name_res_id = fields.Char(string="Model name res id", store=True, compute="_compute_model_name_res_id")

    @api.depends('model_name', 'res_id')
    def _compute_model_name_res_id(self):
        for commission_login in self:
            model_name_res_id = ""
            model_name = commission_login.model_name
            res_id = commission_login.res_id
            if model_name and commission_login.res_id:
                try:
                    model_name_res_id = self.env[model_name].browse([res_id]).name
                except Exception as e:
                    _logger.warning(e)
            commission_login.model_name_res_id = model_name_res_id

    @api.onchange('use_default')
    def change_user_default(self):
        for commission_log in self:
            if commission_log.use_default:
                commission_log.default_rate = self.env['res.partner'].get_default_commission_tariff(
                    commission_log.partner_id,
                    commission_log.role_id)

    def get_compute_calculation_rate(self, hour_rate=False, book_date=False):
        self.ensure_one()
        if self.commission_rate_list_id.id:
            return self.commission_rate_list_id.get_tariff_with_given_hour_rate(hour_rate, book_date)
        if self.use_default:
            if self.commission_main_id:
                return self.commission_main_id.get_compute_calculation_rate(hour_rate, book_date)
            if self.commission_id:
                return self.commission_id.get_compute_calculation_rate(hour_rate, book_date)
            else:
                return 0.0
        return self.default_rate

    @api.depends('model_name', 'res_id')
    def _compute_model_res_id_name(self):
        for log in self:
            try:
                model_obj = self.env[log.model_name]
                object = model_obj.with_context({'active_test': False}).search([('id', '=', log.res_id)])
                if object:
                    log.model_res_id_name = str(
                        self.get_model_names_for_commission_log().get(log.model_name)) + ' ' + object.name
            except Exception as e:
                _logger.warning(_('Error by computing name of log %s with exception %s') % (log, e))
                log.model_res_id_name = "?"

    @api.depends('commission_id.payment_by', 'commission_main_id.commission_id.payment_by')
    def _compute_payment_by(self):
        for log in self:
            payment_by = 'customer'
            if log.commission_main_id.commission_id.id:
                payment_by = log.commission_main_id.commission_id.payment_by
            if log.commission_id.id:
                payment_by = log.commission_id.payment_by
            log.payment_by = payment_by

    def get_commission_tariff(self, hour_line=False):
        self.ensure_one()
        if not self.commission_rate_list_id.id or not hour_line:
            return self.default_rate
        return self.commission_rate_list_id.get_tariff_with_given_hour_rate(hour_line.x_rate, hour_line.date)

    @api.depends('partner_id', 'commission_main_id', 'start_date', 'end_date', 'commission_id.name',
                 'commission_main_id.name')
    def _compute_name(self):
        for log in self:
            name = ''
            if log.partner_id.id:
                name = ' ' + log.partner_id.name
            if log.commission_main_id.id:
                name += ' ' + log.commission_main_id.commission_id.name
            if not log.commission_main_id.id and len(log.commission_id.name or '') > 0:
                name += ' ' + log.commission_id.name
            if not log.commission_main_id.id and log.commission_id.id:
                name += ' ' + log.commission_id.name
            if log.commission_free_worker_id.id and len(log.commission_free_worker_id.description or '') > 0:
                name += ' ' + log.commission_free_worker_id.description
            if log.commission_rate_list_id.id:
                name += ' ' + log.commission_rate_list_id.name or ''
            if log.start_date:
                name += ' ' + log.start_date.strftime('%d-%m-%Y')
            if log.end_date:
                name += " - " + log.end_date.strftime('%d-%m-%Y')
            log.name = name.strip()

    @api.depends('partner_id', 'role_id')
    def _compute_commission_main_id(self):
        commission_partner_obj = self.env['oi1_commission_partner']
        for log in self:
            if log.commission_main_id.id:
                # 2021_06_22 Commission main_id is already calculated so don't do it again
                continue
            commission_main_id = False
            if log.partner_id.id:
                commission_main_id = commission_partner_obj.get_commission_main(log.partner_id, log.role_id)
            log.commission_main_id = commission_main_id

    @api.depends('end_date')
    def _compute_is_actual(self):
        for commission_log in self:
            is_actual = False
            if commission_log.end_date:
                if commission_log.end_date > datetime.date.today():
                    is_actual = True
            else:
                is_actual = True
            commission_log.is_actual = is_actual

    @api.constrains('start_date', 'end_date')
    def _check_end_date_is_greater_then_start_date(self):
        for commission_log in self:
            if commission_log.end_date and commission_log.start_date:
                if commission_log.end_date < commission_log.start_date:
                    raise exceptions.UserError(_("The enddate %s should be greater then the start date %s") % (
                        commission_log.end_date, commission_log.start_date))

    @staticmethod
    def get_fee_amount_from_commission_log(commission_log):
        if len(commission_log) == 1:
            return commission_log.get_commission_tariff()
        return 0.00

    @api.model
    def set_commission_log(self, model_name, res_id, partner_id, role_id,
                           start_date, end_date, default_rate=0.0, commission_id=False,
                           commission_rate_list_id=False, commission_main_id=False):

        oi1_commission_obj = self.env['oi1_commission']
        oi1_commission_partner_obj = self.env['oi1_commission_partner']
        commission_log = False
        create_new_commission_log = True

        def compute_commission_for_the_commission_log(given_commission_id):
            if not given_commission_id and partner_id.id:
                given_commission_id = oi1_commission_partner_obj.search([('partner_id', '=', partner_id.id),
                                                                         ('commission_role_id', '=', role_id.id),
                                                                         ], limit=1).commission_id
            if not given_commission_id:
                given_commission_id = oi1_commission_obj.search([('commission_role_id', '=', role_id.id)], limit=1)

                # 2021_0820 When there is a partner given then a commission should be provided or calculated
            if not given_commission_id and (partner_id and partner_id.id):
                raise exceptions.UserError(
                    _("There is no commission provided for role %s for partner %s ") % (role_id.name, partner_id.name))
            return given_commission_id

        def compute_use_default_and_default_rate(given_default_rate):
            sub_use_default = True
            if given_default_rate != 0.0:
                sub_use_default = False
            if given_default_rate == 0.0:
                given_default_rate = commission_id.default_rate
            if given_default_rate == partner_id.get_default_commission_tariff(partner_id, role_id, commission_id):
                sub_use_default = True
            return given_default_rate, sub_use_default

        commission_id = compute_commission_for_the_commission_log(commission_id)
        default_rate, use_default = compute_use_default_and_default_rate(default_rate)

        if not self.env.context.get('create_new_commission_log', True):
            create_new_commission_log = False
        if not commission_rate_list_id:
            commission_id.commission_rate_list_id
        if model_name not in self.get_model_names_for_commission_log():
            raise exceptions.UserError(_("The model %s is not used for commissions" % model_name))
        commission_logs = self.get_future_commissions_partner(model_name, res_id, role_id, start_date, commission_id)
        if len(commission_logs) == 1 and not create_new_commission_log and end_date:
            commission_logs.write({'end_date': end_date})
        if len(commission_logs) > 0 and create_new_commission_log:
            commission_logs_with_end_date = commission_logs.filtered(lambda l: l.end_date)
            if len(commission_logs_with_end_date) > 0:
                raise exceptions.UserError(_(" Please adjust the commission in het logs because "
                                             "there is already a commission %s with a enddate %s ") %
                                           (commission_logs_with_end_date[0].name,
                                            commission_logs_with_end_date[0].end_date))
            if len(commission_logs) > 2:
                raise exceptions.UserError(_(" Contact the Odoo application manager there are more then 2 logs found"))
            if self._are_adjustments_equal_with_last_current_log(commission_logs, partner_id, start_date, end_date,
                                                                 default_rate, commission_id, commission_rate_list_id,
                                                                 role_id):
                return commission_logs
            old_end_date = start_date - datetime.timedelta(days=1)
            if commission_logs.start_date > old_end_date:
                # 2021_1011 When the end_date will be less then the startdate which is as default the current_date then the commission in the log is never used and can be deleted. This gives
                # the user room for adjustments
                commission_logs.sudo().unlink()
            else:
                commission_logs.end_date = old_end_date
        if partner_id:
            id_commission_rate_list = False
            id_commission_main_id = False
            if commission_rate_list_id:
                id_commission_rate_list = commission_rate_list_id.id
            if commission_main_id:
                id_commission_main_id = commission_main_id.id
            if create_new_commission_log:
                start_date = self._set_start_date_first_commission_record(model_name, res_id, start_date, commission_id)
                commission_log = self.create({'model_name': model_name,
                                              'res_id': res_id,
                                              'partner_id': partner_id.id,
                                              'role_id': role_id.id,
                                              'start_date': start_date,
                                              'end_date': end_date,
                                              'default_rate': default_rate,
                                              'use_default': use_default,
                                              'commission_id': commission_id.id,
                                              'commission_rate_list_id': id_commission_rate_list,
                                              'commission_main_id': id_commission_main_id
                                              })
        return commission_log

    """
        2022_0510 When creating the first commission there will be 14 days substracted from the given start_date. This 
                  makes sure that the commissions will be calculated when a user of order will be generated in the backoffice later. 
    """

    def _set_start_date_first_commission_record(self, model_name, res_id, start_date, commission_id):
        if not start_date:
            start_date = datetime.date.today()
        if not model_name or not res_id or not commission_id:
            _logger.warning("Not all values for model_name, res_id and start_date are given so start_date is returned")
            return start_date
        commissions = self.search([('model_name', '=', model_name),
                                   ('res_id', '=', res_id),
                                   ('commission_id', '=', commission_id.id)]
                                  )
        if len(commissions) == 0:
            start_date = start_date - datetime.timedelta(days=14)
        return start_date

    @staticmethod
    def _are_adjustments_equal_with_last_current_log(commission_log, partner_id, start_date, end_date, default_rate,
                                                     commission_id, commission_rate_list_id, role_id):
        id_commission_rate_list = False
        if commission_rate_list_id:
            id_commission_rate_list = commission_rate_list_id.id
        if commission_log.partner_id == partner_id and \
                commission_log.start_date == start_date and \
                commission_log.end_date == end_date and \
                commission_log.default_rate == default_rate and \
                commission_log.commission_id.id == commission_id.id and \
                commission_log.commission_rate_list_id.id == id_commission_rate_list and \
                commission_log.role_id == role_id:
            return True
        return False

    @api.model
    def get_future_commissions_partner(self, model_name, res_id, role_id, start_date, commission_id):
        free_worker_pay_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_free_worker_commission')
        partners = self.search([('model_name', '=', model_name),
                                ('res_id', '=', res_id),
                                ('role_id', '=', role_id.id),
                                ])
        if role_id.id == free_worker_pay_role.id:
            partners = self.search([('model_name', '=', model_name),
                                    ('res_id', '=', res_id),
                                    ('commission_id', '=', commission_id.id),
                                    ])
        partners = partners.filtered(lambda l: (l.end_date or datetime.date(9999, 12, 31)) > start_date)
        return partners

    @api.model
    def get_commission_partner(self, model_name, res_id, role_id, date):
        if not role_id:
            return self.search([('id', '=', -1)])
        partners = self.search([('model_name', '=', model_name),
                                ('res_id', '=', res_id),
                                ('role_id', '=', role_id.id)
                                ])
        partners = partners.filtered(lambda l: l.start_date <= date < (l.end_date or datetime.date(9999, 12, 31)))
        if len(partners) > 1:
            raise exceptions.UserError(_("Error in gathering commission data. There are more than 1 partners found." +
                                         " Contact the Odoo application manager "))
        return partners

    def get_model_names_for_commission_log(self):
        model_names = {}
        model_names['res.partner'] = _('contact')
        model_names['sale.order'] = _('sale_order')
        model_names['oi1_free_worker'] = _('free worker')
        model_names['oi1_freeworkerpoule'] = _('free worker poule')
        return model_names
