from odoo import models, fields, api, exceptions, _
import datetime


class CommissionFreeWorker(models.Model):
    _name = "oi1_commission_free_worker"
    _description = "Commission free worker"
    _inherits = {'oi1_commission_main': 'main_id'}

    main_id = fields.Many2one('oi1_commission_main', required=True, ondelete='restrict', auto_join=True)
    free_worker_id = fields.Many2one('oi1_free_worker', required=True)
    start_date = fields.Date(string="Startdate", required=True, default=fields.Date.today())
    end_date = fields.Date(string="Enddate")
    active = fields.Boolean(string="Active", default=True)
    description = fields.Char(string="Description",
                              help="The description of the commission. Could be the car, house or the insurence number",
                              default='')

    @api.model
    def get_valid_end_date(self, end_date):
        if end_date:
            return end_date
        return datetime.datetime.strptime('12-31-9999', '%m-%d-%Y').date()

    @api.constrains('end_date', 'start_date')
    def _check_end_date(self):
        for free_worker_commission in self:
            if self.get_valid_end_date(free_worker_commission.end_date) < free_worker_commission.start_date:
                raise exceptions.UserError(
                    _("The commission %s should have a larger end date then a start date") % free_worker_commission.commission_id.name)

    @api.constrains('start_date')
    def check_start_date(self):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        for free_worker_commission in self:
            commissions = oi1_commission_log_obj.search([
                ('res_id', '=', free_worker_commission.free_worker_id.id),
                ('model_name', '=', 'oi1_free_worker'),
                ('commission_id', '=', free_worker_commission.commission_id.id),
            ]).filtered(lambda l: self.get_valid_end_date(l.end_date) > free_worker_commission.start_date)
            if len(commissions) > 1:
                raise exceptions.UserError(
                    _("The commission %s should be unique for each free worker within a time period. \n"
                      "Commission is already used within this period (See commission logs)") % free_worker_commission.commission_id.name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'free_worker_id' in vals:
                vals['partner_id'] = self.env['oi1_free_worker'].browse([vals['free_worker_id']]).partner_id.id
        commission_free_workers = super().create(vals_list)
        self.set_commission_log(commission_free_workers)
        return commission_free_workers

    def write(self, values):
        if 'free_worker_id' in values:
            values['partner_id'] = self.env['oi1_free_worker'].browse([values['free_worker_id']]).partner_id.id
        result = super().write(values)
        if result:
            self.set_commission_log(self)
        return result

    def unlink(self):
        for commission_free_worker in self:
            end_date = commission_free_worker.end_date
            if not end_date or end_date > datetime.date.today():
                end_date = datetime.date.today()
            if end_date < commission_free_worker.start_date:
                end_date = commission_free_worker.start_date
        return self.write({'active': False, 'end_date': end_date})

    @api.model
    def set_commission_log(self, commission_free_workers):
        ### 2021_0921 Check if there is only one active commission

        def check_on_double_commissions(free_worker, commission_id):
            commissions = free_worker.commission_free_worker_ids. \
                filtered(lambda l: l.commission_id.id == commission_id.id)
            if len(commissions) > 1:
                raise exceptions.UserError(_("A commission should be unique for each free worker"))

        commission_log_obj = self.env['oi1_commission_log']
        free_worker_commission_role_id = self.env.ref(
            'oi1_werkstandbij_commission.oi1_commission_role_free_worker_commission')
        model_name = 'oi1_free_worker'
        commission_free_workers._archive_old_commissions()
        for commission_free_worker in commission_free_workers:
            check_on_double_commissions(commission_free_worker.free_worker_id, commission_free_worker.commission_id)
            commisson_log = False
            commisson_logs = commission_log_obj.search([('commission_free_worker_id', '=', commission_free_worker.id)])
            if len(commisson_logs) > 0:
                commisson_log = commisson_logs[0]
                commission_free_worker._synchronize_commission_log(commisson_log)
            if not commisson_log:
                commisson_log = commission_log_obj.with_context(
                    {'create_new_commission_log': commission_free_worker.active}). \
                    set_commission_log(model_name,
                                       commission_free_worker.free_worker_id.id,
                                       commission_free_worker.partner_id,
                                       free_worker_commission_role_id,
                                       commission_free_worker.start_date,
                                       commission_free_worker.end_date,
                                       commission_free_worker.default_rate,
                                       commission_free_worker.commission_id,
                                       commission_free_worker.main_id.commission_rate_list_id,
                                       commission_free_worker.main_id)
                if commisson_log:
                    commisson_log.write({'commission_free_worker_id': commission_free_worker.id})
                    commisson_log._compute_name()

    def _synchronize_commission_log(self, commission_log):
        self.ensure_one()
        if commission_log.commission_id.id != self.commission_id.id:
            raise exceptions.UserError(_("The commission can not be changed"))
        commission_log.end_date = self.end_date
        commission_log.start_date = self.start_date
        commission_log.partner_id = self.partner_id,
        commission_log.default_rate = self.default_rate

    def _archive_old_commissions(self):
        self.mapped('free_worker_id').commission_free_worker_ids.filtered(
            lambda l: l.end_date and l.end_date < datetime.date.today()).active = False

