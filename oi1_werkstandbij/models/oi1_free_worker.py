from odoo import models, fields, api, _
import datetime
import logging

_logger = logging.getLogger(__name__)

class FreeWorker(models.Model):
    _inherit = 'oi1_free_worker'

    default_bank_partner_id = fields.Many2one('res.partner', compute="_compute_bank_partner_id")
    date_last_worked = fields.Date(string="Date last worked")
    date_first_worked = fields.Date(string="First work day")
    worked_hours = fields.Integer(string="Booked hours", compute="_compute_worked_hours")
    booked_hours = fields.One2many('account.analytic.line', compute="_compute_booked_hours")
    account_move_ids = fields.One2many('account.move', compute="_compute_account_move_ids")
    qty_account_move_ids = fields.Integer(string="Invoice count", compute="_compute_qty_account_move_ids")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res.update({
            'x_has_vat_on_invoice': False
            })
        return res


    def compute_first_and_last_work_day(self):
        account_analytic_line_obj = self.env['account.analytic.line']
        for free_worker in self:
            work_day = False
            account_analytic_lines = account_analytic_line_obj.search([('x_free_worker_id', '=', free_worker.id)],
                                                                      order="date asc", limit=1)
            if len(account_analytic_lines) > 0:
                work_day = account_analytic_lines[0].date
            free_worker.date_first_worked = work_day
            account_analytic_lines = account_analytic_line_obj.search([('x_free_worker_id', '=', free_worker.id)],
                                                                      order="date desc", limit=1)
            if len(account_analytic_lines) > 0:
                work_day = account_analytic_lines[0].date
            free_worker.date_last_worked = work_day

    def _compute_qty_account_move_ids(self):
        for free_worker in self:
            free_worker.qty_account_move_ids = len(free_worker.account_move_ids)

    def _compute_account_move_ids(self):
        account_move_obj = self.env['account.move']
        for free_worker in self:
            free_worker.account_move_ids = account_move_obj.search([('partner_id', '=', free_worker.partner_id.id)])

    def _compute_booked_hours(self):
        account_analytic_line_obj = self.env['account.analytic.line']
        for free_worker in self:
            free_worker.booked_hours = account_analytic_line_obj.search(
                [('x_free_worker_id', '=', free_worker.id)])

    def _compute_worked_hours(self):
        for free_worker in self:
            free_worker.worked_hours = len(free_worker.booked_hours)

    def do_button_free_invoices(self):
        return {
            'name': _('Free worker invoices'),
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.account_move_ids.ids)],
            'options': {'no_create': True, 'no_create_edit': True},
            'view_mode': 'tree,form',
            'view_id': False,
            'context': {'create': False, 'edit': False},
        }

    def do_button_free_worker_hours(self):
        account_analytic_line_tree_view_id = self.env.ref('oi1_werkstandbij.view_account_analytic_line_tree').id
        return {
            'name': _('Free worker hours'),
            'res_model': 'account.analytic.line',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.booked_hours.ids)],
            'options': {'no_create': True, 'no_create_edit': True},
            'view_mode': 'tree',
            'view_id': False,
            'context': {'create': False, 'edit': False},
            'views': [(account_analytic_line_tree_view_id, 'tree')],
        }

    def _compute_bank_partner_id(self):
        for free_worker in self:
            free_worker.default_bank_partner_id = free_worker.partner_id

    def compute_state(self):
        super().compute_state()
        for free_worker in self:
            if free_worker.state == "checked" and free_worker.date_last_worked and free_worker.date_last_worked > \
                    datetime.date.today() - datetime.timedelta(days=90):
                free_worker.state = "active"
            if free_worker.state == "active" and free_worker.date_last_worked and free_worker.date_last_worked < \
                    datetime.date.today() - datetime.timedelta(days=360):
                free_worker.state = "old"
            if free_worker.state in ('concept','checked') \
                    and free_worker.registration_date < datetime.date.today() - datetime.timedelta(days=180):
                free_worker.state = "old"

    def set_date_last_worked(self, hour_line):
        for free_worker in self:
            free_worker.compute_state()
            if not free_worker.date_last_worked or free_worker.date_last_worked < hour_line.date:
                free_worker.date_last_worked = hour_line.date

    @api.model
    def do_calculate_status_free_workers_cron(self):
        _logger.info("Starting calculating current state of free workers")
        free_worker_obj = self.env['oi1_free_worker']
        for free_worker in free_worker_obj.search([('state', '!=', 'old')]):
            free_worker.sudo().compute_first_and_last_work_day()
            free_worker.sudo().compute_state()
        _logger.info("Finished calculating current state of free workers")
