from odoo import models, api, exceptions, _
from datetime import date

import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @staticmethod
    def get_wsb_payment_term(payment_term, payment_term_obj, payment_company_id):
        if not payment_term.name:
            return False
        payment_terms = payment_term_obj.sudo().search([('company_id', '=', payment_company_id),
                                                        ('name', '=', payment_term.name)], limit=1)
        if len(payment_terms) == 0:
            raise exceptions.UserError(_(" Payment term with description %s not found within the payment company %s")
                                       % (payment_term.name, 'WSB'))
        return payment_terms[0]

    def do_prepare_payment_wsb(self):
        for account_invoice in self:
            if account_invoice.state == 'draft':
                account_invoice.action_post()
            self._process_freeworker_invoices_and_commissions(account_invoice)
            account_invoice.state = 'Start_Factoring'
            return self.send_emails_to_partners(account_invoice)

    @api.model
    def _process_freeworker_invoices_and_commissions(self, account_invoice):
        oi1_commission_invoice_helper_obj = self.env['oi1_commission_invoice_helper']
        invoice_free_worker_wizard = self.env['oi1_werkstandbij.invoice_free_worker_wizard']
        hour_lines = account_invoice.x_sale_account_analytic_line_ids
        invoice_free_worker_wizard.create_free_worker_invoices_from_customer_invoices(hour_lines)
        oi1_commission_invoice_helper_obj.do_create_commissions(hour_lines)

    def send_emails_to_partners(self, account_move):
        commission_payment_obj = self.env['oi1_sale_commission_payment']
        commission_payments = commission_payment_obj.sudo().search([('invoice_id', '=', account_move.id)])
        if len(commission_payments) > 0:
            return account_move.action_invoice_sent()
        if account_move.x_sale_invoice_analytic_line_count > 0:
            return account_move.action_invoice_sent()
        if account_move.x_pur_invoice_analytic_line_count > 0:
            return account_move.do_email_freeworker_specification()
        return True

