from odoo import models, api, fields, exceptions, _
from datetime import date

import logging

_logger = logging.getLogger(__name__)


class CommissionInvoiceHelper(models.TransientModel):
    _inherit = "oi1_commission_invoice_helper"

    account_analytic_line_id = fields.Many2one('account.analytic.line')
    customer_fee = fields.Float(string="Customer fee", compute="_compute_commission_ids")
    gross_margin = fields.Float(string="Gross margin", compute="_compute_commission_ids")
    commission_amount = fields.Float(string="Commission amount", compute="_compute_commission_ids")
    account_manager_partner_id = fields.Many2one('res.partner', string="Account manager",
                                                 compute="_compute_commission_ids")
    nett_margin = fields.Float(string="Nett margin", compute="_compute_nett_margin")
    commission_payment_log_ids = fields.Many2many('oi1_commission_payment_log')

    @api.model
    def get_commission_payment_logs(self, account_analytic_line):

        """
        2021_0629 Splits the commission in the different sub commissions which can be defined on the commission level
        """

        def split_payment_logs_in_sub_commissions():
            for commission_log_id in commission_log_ids:
                for sub_commission in commission_log_id.commission_id.sub_commission_ids:
                    commission_payment_log_obj.create({
                        'commission_log_id': commission_log_id.id,
                        'account_analytic_account_id': account_analytic_line.id,
                        'is_sub_commission': True,
                        'commission_id': sub_commission.id,
                    })

        commission_payment_log_obj = self.env['oi1_commission_payment_log']
        commission_payment_logs = commission_payment_log_obj.search(
            [('account_analytic_account_id', '=', account_analytic_line.id)])
        if len(commission_payment_logs.filtered(lambda l: l.commission_payment_line_id.ids)) > 0:
            return commission_payment_logs
        commission_payment_logs.unlink()
        commission_log_ids = self.get_commissions_on_analytic_hour_worker(account_analytic_line)
        for commission_log_id in commission_log_ids:
            commission_id = commission_log_id.commission_id
            if not commission_id:
                commission_id = commission_log_id.commission_main_id.commission_id
            if not commission_id:
                raise exceptions.UserError(
                    _("No commission found on the commissionlog %s %s. Please make sure there is a commission")
                    % (commission_log_id.name, commission_log_id))
            commission_payment_log_obj.create({'commission_log_id': commission_log_id.id,
                                               'account_analytic_account_id': account_analytic_line.id,
                                               'commission_id': commission_id.id,
                                               })
        split_payment_logs_in_sub_commissions()
        commission_payment_logs = commission_payment_log_obj.search(
            [('account_analytic_account_id', '=', account_analytic_line.id)])
        return commission_payment_logs

    @api.onchange('account_analytic_line_id')
    def _compute_commission_ids(self):
        for wizard in self:
            commission_payment_log_ids = wizard.sudo().get_commission_payment_logs(self.account_analytic_line_id)
            wizard.customer_fee = wizard.account_analytic_line_id.get_sales_tariff()
            wizard.gross_margin = wizard.account_analytic_line_id.get_gross_margin()
            wizard.account_manager_partner_id = wizard.account_analytic_line_id.get_account_manager()
            commission_amount = 0.0
            for payment_commission_log_id in commission_payment_log_ids.filtered(
                    lambda l: l.commission_log_id.commission_id.payment_by == 'customer'):
                commission_amount += payment_commission_log_id.calculated_rate
            wizard.commission_amount = commission_amount
            wizard.nett_margin = wizard.gross_margin - wizard.commission_amount
            wizard.write({'commission_payment_log_ids': [(6, 0, commission_payment_log_ids.ids)]})

    @api.model
    def get_commissions_on_analytic_hour_worker(self, hour_line):
        # account_manager_role = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_account_manager')
        commission_log_obj = self.env['oi1_commission_log']
        free_worker_obj = self.env['oi1_free_worker']

        commission_logs = commission_log_obj.search([('id', '=', -1)])
        free_worker_id = free_worker_obj.search([('partner_id', '=', hour_line.x_partner_id.id)])
        if not free_worker_id.id:
            raise exceptions.UserError(
                _(
                    "Partner %s is not a freeworker so the commission couldn't be calculated" % hour_line.x_partner_id.name))
        commission_logs += self.get_commissions_on_free_worker(free_worker_id, hour_line.date)
        commission_logs += self.get_commissions_on_sale_order(hour_line.x_sale_id, hour_line.date)
        commission_logs += self.get_commissions_on_poule(hour_line.x_poule_id, hour_line.date)
        commission_logs += self.get_free_worker_commissions(free_worker_id, hour_line.date)
        # 2021_0920 Disabled
        # commission_logs = commission_logs.filtered(lambda l: l.commission_main_id.commission_id.commission_role_id.id != account_manager_role.id)
        return commission_logs

    @api.model
    def do_create_commissions(self, hour_lines):
        # 2021_0902 Make sure that commissions are only once created on a hourline
        hour_lines = hour_lines.filtered(lambda l: not l.x_commission_created and l.x_sale_id.id)
        self.set_commission_payment_lines_customer(hour_lines)
        self.set_commission_payment_lines_freeworker(hour_lines)
        self.create_reservering_on_commission_payments(hour_lines)
        hour_lines.write({'system': 1, 'x_commission_created': True})

    @api.model
    def create_reservering_on_commission_payments(self, hour_lines):
        def get_sale_commission_reservation_partner(sub_partner_id):
            sub_sale_commission_payment = False
            if not sub_partner_id.id:
                raise UserWarning(_("No value given for parameter partner_id"))
            sale_commission_payment_obj = self.env['oi1_sale_commission_payment']
            sale_commission_payments = sale_commission_payment_obj.search([('partner_id', '=', sub_partner_id.id),
                                                                           ('type', '=', 'reservation'),
                                                                           ('state', 'in', ['concept', 'approved'])
                                                                           ])
            if len(sale_commission_payments) > 0:
                sub_sale_commission_payment = sale_commission_payments[0]
            if not sub_sale_commission_payment:
                name = _("Reservation for partner %s " % partner_id.name)
                sub_sale_commission_payment = sale_commission_payment_obj.create({'partner_id': sub_partner_id.id,
                                                                                  'type': 'reservation',
                                                                                  'state': 'approved',
                                                                                  'name': name})
            return sub_sale_commission_payment

        def set_commission_payment_line(sale_commission_payment, sub_reservation_amount, sub_name, sub_id,
                                        source_sale_commission_payment_line):

            def set_source_commission_payment_line(sub_source_sale_commission_payment_line,
                                                   sub_sale_commission_payment_line):
                sub_source_sale_commission_payment_line.reservation_commission_payment_line_id = sub_sale_commission_payment_line
                sub_source_sale_commission_payment_line.rate -= sub_sale_commission_payment_line.rate
                sub_source_sale_commission_payment_line.amount -= abs(
                    sub_sale_commission_payment_line.rate * source_sale_commission_payment_line.qty)

            sale_commission_payment_line_obj = self.env['oi1_sale_commission_payment_line']
            commission = self.env.ref('oi1_werkstandbij.oi1_commission_reservation')
            code = 'oi1_freeworkerpoule.' + str(sub_id)
            sale_commission_payment_line = False

            sale_commission_payment_lines = sale_commission_payment_line_obj.search(
                [('oi1_sale_commission_id', '=', sale_commission_payment.id),
                 ('code', '=', code),
                 ('commission_id', '=', commission.id),
                 ('type', '=', 'reservation'),
                 ('rate', '=', sub_reservation_amount),
                 ])
            if len(sale_commission_payment_lines) > 0:
                sale_commission_payment_line = sale_commission_payment_lines[0]
            if not sale_commission_payment_line:
                sale_commission_payment_line = sale_commission_payment_line_obj.create(
                    {'oi1_sale_commission_id': sale_commission_payment.id,
                     'rate': sub_reservation_amount,
                     'qty': 0,
                     'name': sub_name,
                     'code': code,
                     'commission_id': commission.id,
                     'unit': 'qty',
                     'type': 'reservation'
                     })
            sale_commission_payment_line.qty += source_sale_commission_payment_line.qty
            sale_commission_payment_line.amount = sale_commission_payment_line.qty * sale_commission_payment_line.rate
            set_source_commission_payment_line(source_sale_commission_payment_line, sale_commission_payment_line)
            return sale_commission_payment_line

        oi1_commission_role_obj = self.env['oi1_commission_role']
        free_worker_poole_obj = self.env['oi1_freeworkerpoule']
        sale_order_obj = self.env['sale.order']

        role_poole_manager = oi1_commission_role_obj.get_poule_manager_role()
        role_account_manager = oi1_commission_role_obj.get_account_manager_role()

        poole_commission_logs = hour_lines.x_commission_payment_line_ids.commission_payment_log_id. \
            commission_log_id.filtered(lambda l: l.role_id.id == role_poole_manager.id and
                                                 l.model_name == 'oi1_freeworkerpoule')
        for poole_commission_log in poole_commission_logs:
            res_id = poole_commission_log.res_id
            free_worker_poole = free_worker_poole_obj.search([('id', '=', res_id)])
            if free_worker_poole.reservation_amount != 0.0:
                x_commission_payment_line_ids = hour_lines.x_commission_payment_line_ids. \
                    filtered(lambda l: l.commission_payment_log_id.commission_log_id.id == poole_commission_log.id)
                if len(x_commission_payment_line_ids) > 0:
                    partner_id = x_commission_payment_line_ids[0].oi1_sale_commission_id.partner_id
                    sale_commission_payment = get_sale_commission_reservation_partner(partner_id)
                    for x_commission_payment_line_id in x_commission_payment_line_ids:
                        set_commission_payment_line(sale_commission_payment, free_worker_poole.reservation_amount,
                                                    free_worker_poole.name, free_worker_poole.id, x_commission_payment_line_id)

        sale_order_commission_logs = hour_lines.x_commission_payment_line_ids.commission_payment_log_id.commission_log_id.filtered(
            lambda l: l.role_id.id == role_account_manager.id
                      and l.model_name == 'sale.order')

        for sale_order_commission_log in sale_order_commission_logs:
            res_id = sale_order_commission_log.res_id
            sale_order = sale_order_obj.search([('id', '=', res_id)])
            if sale_order.x_reservation_amount != 0.0:
                x_commission_payment_line_ids = hour_lines.x_commission_payment_line_ids. \
                    filtered(lambda l: l.commission_payment_log_id.commission_log_id.id == sale_order_commission_log.id)
                if len(x_commission_payment_line_ids) > 0:
                    partner_id = x_commission_payment_line_ids[0].oi1_sale_commission_id.partner_id
                    sale_commission_payment = get_sale_commission_reservation_partner(partner_id)
                    for x_commission_payment_line_id in x_commission_payment_line_ids:
                        set_commission_payment_line(sale_commission_payment, sale_order.x_reservation_amount,
                                                    sale_order.name, sale_order.id, x_commission_payment_line_id)


    @api.model
    def set_commission_payment_lines_customer(self, hour_lines):
        return self._set_commission_payment_lines_by_type_customer(hour_lines, 'customer')

    @api.model
    def set_commission_payment_lines_freeworker(self, hour_lines):
        invoice_line_obj = self.env['account.move.line']
        invoice_line_values = {}
        if len(hour_lines) == 0:
            return
        for hour_line in hour_lines:
            commission_payment_log_ids = self.get_commission_payment_logs(hour_line).filtered(
                lambda l: l.commission_id.payment_by == 'freeworker')
            self.set_invoice_values_from_commission_payment_log(commission_payment_log_ids,
                                                                hour_line,
                                                                invoice_line_values,
                                                                )
        invoice_lines = invoice_line_obj.create_account_invoice_move_line(invoice_line_values.values())

        invoice_lines.set_vat_move_line_for_free_worker()
        self._set_commission_payment_lines_by_type_customer(hour_lines, payment_type='freeworker')

    @api.model
    def _find_free_worker_invoice(self, partner_id):
        journal_id = self.env.ref('oi1_werkstandbij.workerspayment_journal').id
        account_move_obj = self.env['account.move']
        invoices = account_move_obj.sudo().search([('partner_id', '=', partner_id.id),
                                                   ('state', '=', 'draft'),
                                                   ('move_type', '=', 'in_invoice'),
                                                   ('company_id', '=', self.env.company.id),
                                                   ('journal_id', '=', journal_id),
                                                   ])
        if len(invoices) == 0:
            raise exceptions.UserError(_("No valid invoice found for freeworker %s. Please make a invoice ")
                                     % partner_id.name)
        return invoices[0]

    @api.model
    def set_invoice_values_from_commission_payment_log(self, commission_payment_log_ids, hour_line, map_values):
        for commission_payment_log_id in commission_payment_log_ids:
            partner_id = hour_line.x_partner_id
            account_move = self._find_free_worker_invoice(partner_id)
            product_id = commission_payment_log_id.commission_id.product_id
            values = {'move_id': account_move.id}
            values['product_id'] = product_id.id
            commission_payment_log_id._compute_calculated_rate()
            values['price_unit'] = -commission_payment_log_id.calculated_rate
            values['quantity'] = hour_line.unit_amount
            values['name'] = commission_payment_log_id.commission_id.name
            values[
                'account_id'] = product_id.property_account_expense_id.id or product_id.categ_id.property_account_expense_categ_id.id
            key = str(values['move_id']) + "." + str(values['product_id']) + "." + str(values['price_unit'])
            old_values = map_values.get(key, False)
            if old_values:
                old_values['quantity'] = old_values['quantity'] + values['quantity']
                map_values[key] = old_values
            if not old_values:
                map_values[key] = values
            commission_payment_log_id.write({'payment_move_id': account_move.id})
        return map_values

    @api.model
    def _set_commission_payment_lines_by_type_customer(self, hour_lines, payment_type='customer'):
        sale_commission_payment_line_obj = self.env['oi1_sale_commission_payment_line']
        line_values = []
        if len(hour_lines) == 0:
            return
        for hour_line in hour_lines:
            commission_payment_log_ids = self.get_commission_payment_logs(hour_line).filtered(
                lambda l: l.commission_id.payment_by == payment_type)
            hour_values = self._get_hour_values_from_line(hour_line)
            values = self._get_commission_payment_lines_values(commission_payment_log_ids,
                                                               hour_values)
            if len(values) > 0:
                line_values = line_values + values
        if len(line_values) > 0:
            return sale_commission_payment_line_obj.create(line_values)
        return sale_commission_payment_line_obj.search([('id', '=', -1)])

    @staticmethod
    def _get_hour_values_from_line(hour_lines):
        for hour_line in hour_lines:
            name = hour_line.name + ' ' + fields.Date.to_string(hour_line.date) + ' ' + hour_line.x_partner_id.name
            return {'unit_amount': hour_line.unit_amount,
                    'date': hour_line.date,
                    'sale_id': hour_line.x_sale_id.id,
                    'x_partner_id': hour_line.x_partner_id.id,
                    'id': hour_line.id,
                    'name': name}

    @api.model
    def _get_commission_payment_lines_values(self, commission_payment_log_ids, hour_values=False):
        list_values = []
        for commission_payment_log in commission_payment_log_ids:
            book_date = date.today()
            if 'date' in hour_values:
                book_date = hour_values['date']
            qty = False
            if 'unit_amount' in hour_values:
                qty = hour_values['unit_amount']
            if not qty:
                raise exceptions.UserError(_("There is not provided qty for commission %s") % commission_payment_log)
            rate = commission_payment_log.calculated_rate
            amount = qty * rate
            if commission_payment_log.commission_id.commission_beneficiary_partner_id:
                _logger.debug("Commission is going to %s %s", (commission_payment_log.commission_id.name,
                                                               commission_payment_log.commission_id.commission_beneficiary_partner_id))
            partner_id = commission_payment_log.commission_id.commission_beneficiary_partner_id or commission_payment_log.partner_id
            values = {'oi1_sale_commission_id': self.get_partner_commission(partner_id, book_date).id,
                      'date': book_date,
                      'qty': qty,
                      'rate': rate,
                      'type': 'commission',
                      'amount': amount}
            if 'sale_id' in hour_values:
                values['sale_id'] = hour_values['sale_id']
            if not commission_payment_log.commission_id.id:
                raise exceptions.UserError(_("Commmision log %s has no commission") % commission_payment_log)
            values['commission_id'] = commission_payment_log.commission_id.id
            if 'x_partner_id' in hour_values:
                values['partner_worker_id'] = hour_values['x_partner_id']
            if 'id' in hour_values:
                values['account_analytic_line_id'] = hour_values['id']
            values['name'] = hour_values['name']
            values['commission_payment_log_id'] = commission_payment_log.id
            list_values.append(values)
        return list_values

    @api.model
    def get_commissions_on_sale_order(self, sale_order, reg_date=False):
        return super().get_commissions_on_sale_order(sale_order, reg_date) + self.get_wsb_ssf_commission(sale_order)

    @api.model
    def get_wsb_ssf_commission(self, sale_order, reg_date=False):
        if not reg_date:
            reg_date = date.today()

        commission_log_obj = self.env['oi1_commission_log']
        oi1_commission_wsb_ssf_role = self.env.ref('oi1_werkstandbij.oi1_commission_role_wsb_ssf')

        commission_logs = commission_log_obj.search([('model_name', '=', 'sale.order'),
                                                     ('res_id', '=', sale_order.id), ])
        commission_logs_filtered = self._filter_commission_logs(commission_logs,
                                                                oi1_commission_wsb_ssf_role
                                                                , reg_date)
        if len(commission_logs_filtered) == 0:
            role_id = self.env.ref('oi1_werkstandbij.oi1_commission_role_wsb_ssf')
            partner_id = self.env.company.partner_id
            commission_logs_filtered = sale_order._set_sale_order_commission_ids(sale_order.id, partner_id, role_id)
        return commission_logs_filtered
