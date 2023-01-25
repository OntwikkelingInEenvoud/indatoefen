import datetime

from odoo import models, api
from datetime import date

import logging
_logger = logging.getLogger(__name__)


class CommissionInvoiceHelper(models.TransientModel):
    _name = "oi1_commission_invoice_helper"
    _description = "Commission Invoice helper"


    @api.model
    def get_commissions_on_free_worker(self, free_worker_id, reg_date=False):
        if not reg_date:
            reg_date = date.today()
        commission_role_obj = self.env['oi1_commission_role']
        commission_log_obj = self.env['oi1_commission_log']

        mediator_role = commission_role_obj.get_mediator_role()
        recruiter_role = commission_role_obj.get_recruiter_role()
        practical_work_planner_role = commission_role_obj.get_practical_work_planner_role()

        commission_logs = self.env['oi1_commission_log']
        commission_free_worker_logs = commission_log_obj.sudo().search([('model_name', '=', 'oi1_free_worker'),
                                                          ('res_id', '=', free_worker_id.id),
                                                          ])
        commission_logs += self._filter_commission_logs(commission_free_worker_logs, mediator_role, reg_date)
        commission_logs += self._filter_commission_logs(commission_free_worker_logs, recruiter_role, reg_date)
        commission_logs += self._filter_commission_logs(commission_free_worker_logs, practical_work_planner_role, reg_date)
        return commission_logs

    @api.model
    def _filter_commission_logs(self, commission_logs, role_id, reg_date):
        commission_logs = commission_logs.filtered(lambda l: l.role_id.id == role_id.id)
        commission_logs = commission_logs.filtered(
            lambda l: l.start_date <= reg_date and (not l.end_date or l.end_date > reg_date))
        return commission_logs

    @api.model
    def get_commissions_on_sale_order(self, sale_order, date=False):
        commission_role_obj = self.env['oi1_commission_role']
        seller_role = commission_role_obj.get_seller_role()
        account_manager_role = commission_role_obj.get_account_manager_role()
        commission_log_obj = self.env['oi1_commission_log']
        commission_logs = commission_log_obj.search([('id', '=', -1)])
        if not date:
            date = datetime.date.today()

        commission_sale_logs = commission_log_obj.search([('model_name', '=', 'sale.order'),
                                                     ('res_id', '=', sale_order.id),
                                                     ])
        commission_partner_logs = commission_log_obj.search([('model_name', '=', 'res.partner'),
                                                             ('res_id', '=', sale_order.partner_id.id),
                                                             ])
        seller_partner_logs = self._filter_commission_logs(commission_sale_logs, seller_role,date)
        if len(seller_partner_logs) == 0:
            seller_partner_logs = self._filter_commission_logs(commission_partner_logs, seller_role,date)
        commission_logs += seller_partner_logs
        account_manager_logs = self._filter_commission_logs(commission_sale_logs,account_manager_role, date)
        if len(account_manager_logs) == 0:
            account_manager_logs = self._filter_commission_logs(commission_partner_logs, account_manager_role, date)
        commission_logs += account_manager_logs
        return commission_logs

    @api.model
    def get_commissions_on_poule(self, worker_poule, reg_date=False):
        commission_role_obj = self.env['oi1_commission_role']
        commission_log_obj = self.env['oi1_commission_log']
        if not reg_date:
            reg_date = datetime.date.today()
        operational_work_planner_role =  commission_role_obj.get_operational_work_planner_role()
        poule_manager_role = commission_role_obj.get_poule_manager_role()

        commission_logs = commission_log_obj.search([('id', '=', -1)])
        commission_poule_logs = commission_log_obj.search([('model_name', '=', 'oi1_freeworkerpoule'),
                                                          ('res_id', '=', worker_poule.id),])
        operational_work_planner_logs = self._filter_commission_logs(commission_poule_logs, operational_work_planner_role, reg_date)
        commission_logs += operational_work_planner_logs

        poule_manager_logs = self._filter_commission_logs(commission_poule_logs, poule_manager_role, reg_date)
        commission_logs += poule_manager_logs
        return commission_logs

    @api.model
    def get_free_worker_commissions(self, free_worker, book_date=date.today()):
        commission_log_obj = self.env['oi1_commission_log']
        commission_logs = commission_log_obj.search([('id', '=', -1)])
        commission_free_worker_logs = commission_log_obj.search([('model_name', '=', 'oi1_free_worker'),
                                                           ('res_id', '=', free_worker.id), ])
        free_worker_commission_role = self.env.ref(
            'oi1_werkstandbij_commission.oi1_commission_role_free_worker_commission')
        commission_logs += self._filter_commission_logs(commission_free_worker_logs, free_worker_commission_role, book_date)
        return commission_logs

    @api.model
    def split_commission_in_sub_commissions(self, commission_mains):
        for commission_main in commission_mains:
            for sub_commission in commission_main.commission_id.sub_commission_ids:
                commission_main_sub = commission_main.copy()
                commission_main_sub.commission_id = sub_commission
                commission_main_sub.default_rate = sub_commission.default_rate
                commission_mains = commission_mains + commission_main_sub
        return commission_mains

    @api.model
    def get_commissions_payments(self, commission_mains, commission_payments=False):
        if not commission_payments:
            commission_payments = {}
        for partner in commission_mains.mapped('partner_id'):
            if partner.id not in commission_payments:
                commission_payments[partner.id] = self.get_partner_commission(partner)
        return commission_payments

    @api.model
    def get_partner_commission(self, partner_id, book_date=False):
        if not book_date:
            book_date = date.today()
        period = partner_id.get_commission_period(partner_id, book_date)
        commission_obj = self.env['oi1_sale_commission_payment']
        sale_commission_payment = False
        commissions = commission_obj.search([('partner_id', '=', partner_id.id),
                                             ('state', '=', 'concept'),
                                             ('company_id', '=', self.env.company.id),
                                             ('period', '=', period),
                                             ('type', '=', 'commission')
                                             ])
        if len(commissions) > 0:
            sale_commission_payment = commissions[0]
        if not sale_commission_payment:
            name = partner_id.name
            sale_commission_payment = commission_obj.create({'partner_id': partner_id.id,
                                                             'name': name,
                                                             'company_id': self.env.company.id,
                                                             'period': period,
                                                             'type' : 'commission'
                                                             })
        return sale_commission_payment
