import dateutil.utils
from odoo import models, fields, api, Command, _
import datetime

class CreateFreeWorkerInvoices(models.TransientModel):
    _name = "oi1_werkstandbij.invoice_free_worker_wizard"
    _description = "Create invoice for free workers"

    @api.model
    def create_free_worker_invoices_from_customer_invoices(self, hour_lines):
        #2023_0112 Only invoices should be processed which are booked on a free worker and which doesn't have a invoice
        hour_lines = hour_lines.filtered(lambda l: l.x_partner_id.id and not l.x_pur_invoice_line_id.id)
        #2023_0112 Only invoices should be created with are invoiced to a customer
        hour_lines = hour_lines.filtered(lambda l: l.x_sale_invoice_line_id.id)
        dict_invoices = False
        if len(hour_lines) > 0:
            dict_invoices, list_invoice_line_values = self._get_invoices(hour_lines)
            dict_invoice_lines = self._get_purchase_invoice_lines(hour_lines, list_invoice_line_values)
            for partner_id in dict_invoices.keys():
                account_move = dict_invoices[partner_id]
                account_move.with_context(dynamic_unlink=True).write({'line_ids': False})
                for invoice_line_values in dict_invoice_lines[partner_id]:
                    account_move.with_context(system=1).write({'invoice_line_ids': [Command.create(invoice_line_values)],
                                                               'invoice_date': datetime.date.today()})
        if dict_invoices:
            return list(dict_invoices.values())
        return False

    @api.model
    def _get_invoices(self, hour_lines):
        tools_obj = self.env['oi1.object_tools']
        dict_invoices = {}
        dict_invoice_lines = []
        if len(hour_lines) == 0:
            return dict_invoices
        for hour_line in hour_lines:
            partner_id = hour_line.x_partner_id
            if partner_id.id not in dict_invoices:
                dict_invoices = self._add_purchase_invoice_to_dict_invoices(partner_id, dict_invoices)

        for account_move in dict_invoices.values():
            list_invoice_line_values = tools_obj.get_dictionary_values(account_move.invoice_line_ids)
            # 2023_0111 Replace the  move_id to the partner_id because this is mapped later in the invoices
            for invoice_line_values in list_invoice_line_values:
                invoice_line_values['move_id'] = account_move.partner_id.id
                dict_invoice_lines.append(invoice_line_values)
        return dict_invoices, dict_invoice_lines

    def _add_purchase_invoice_to_dict_invoices(self, partner_id, dict_invoices):
        invoice_obj = self.env['account.move']
        invoice = False
        journal_id = self.env.ref('oi1_werkstandbij.workerspayment_journal')
        invoices = invoice_obj.search([('partner_id', '=', partner_id.id),
                                       ('state', '=', 'draft'),
                                       ('move_type', '=', 'in_invoice'),
                                       ('company_id', '=', self.env.company.id),
                                       ('journal_id', '=', journal_id.id)
                                       ], limit=1)
        if len(invoices) > 0:
            invoice = invoices[0]
        if not invoice:
            fiscal_position_id = self.env['account.fiscal.position']._get_fiscal_position(
                partner_id,
                partner_id)
            invoice = invoice_obj.create({'partner_id': partner_id.id,
                                          'move_type': 'in_invoice',
                                          'journal_id': journal_id.id,
                                          'fiscal_position_id': fiscal_position_id,
                                          'company_id': self.env.company.id,
                                          'partner_bank_id': journal_id.company_id.x_default_sales_bankId.id,
                                          })
        dict_invoices.update({partner_id.id: invoice})
        return dict_invoices

    @api.model
    def _get_purchase_invoice_lines(self, hour_lines, list_invoice_lines_values):
        dict_invoice_lines_values_by_move_id = {}
        free_worker_poule_obj = self.env['oi1_freeworkerpoule']
        tools_obj = self.env['oi1.object_tools']
        """
        2021_0629 	Gathers the description on the invoice this will be the name of the main poule if the current 
                    poule has a main poule
        """
        pos = 0
        dict_invoice_lines = {}
        for invoice_line_values in list_invoice_lines_values:
            analytic_account_line_ids = invoice_line_values['x_purchase_analytic_account_line_ids']
            analytic_hour_line = False
            key = False
            pos += 1
            if analytic_account_line_ids:
                analytic_account_line_ids = tools_obj.get_id_list(analytic_account_line_ids)
                if len(analytic_account_line_ids) > 0:
                    analytic_hour_line = self.env['account.analytic.line'].browse([analytic_account_line_ids[0]])
            if analytic_hour_line:
                key = str(analytic_hour_line.x_partner_id.id) + "." + \
                      str(analytic_hour_line.date) + "." + \
                      str(analytic_hour_line.x_rate)
            if not key:
                key = 'QQQQQQ.' + str(pos)
            dict_invoice_lines[key] = invoice_line_values
        for hour_line in hour_lines:
            key = str(hour_line.x_partner_id.id) + "." + \
                  str(hour_line.date) + "." \
                  + str(hour_line.x_rate)
            if key in dict_invoice_lines:
                dict_invoice_lines[key]['quantity'] = dict_invoice_lines[key]['quantity'] + hour_line.unit_amount
                x_purchase_analytic_account_line_ids = dict_invoice_lines[key]['x_purchase_analytic_account_line_ids']
                x_purchase_analytic_account_line_ids.append((4, hour_line.id))
                dict_invoice_lines[key]['x_purchase_analytic_account_line_ids'] = x_purchase_analytic_account_line_ids
            if key not in dict_invoice_lines:
                date = fields.Date.from_string(hour_line.date)
                str_date = ("0" + str(date.day))[-2:] + "-" + ("0" + str(date.month))[-2:] + "-" + str(date.year)
                name = str_date + ' ' + hour_line.x_poule_id.name + ' ' + hour_line.name
                if hour_line.task_id.id:
                    name = name + ' ' + hour_line.task_id.name
                product = hour_line.x_poule_id.product_id
                account_id = product.property_account_expense_id or product.categ_id.property_account_expense_categ_id
                dict_invoice_lines[key] = {'quantity': hour_line.unit_amount,
                                           'price_unit': hour_line.x_rate,
                                           'product_id': product.id,
                                           'account_id': account_id.id,
                                           'name': name,
                                           'x_del_date': hour_line.date,
                                           'x_sale_id': hour_line.x_sale_id.id,
                                           'x_purchase_analytic_account_line_ids': [(4, hour_line.id)],
                                           'move_id': hour_line.x_partner_id.id,
                                           'display_type': 'product',
                                           'tax_ids': False,
                                           }
                tax_ids = self.get_free_worker_taxes(hour_line, account_id)
                if tax_ids:
                    dict_invoice_lines[key]['tax_ids'] = [(6, 0, tax_ids)]
        for sorted_key in sorted(dict_invoice_lines):
            invoice_line_values = dict_invoice_lines[sorted_key]
            key = invoice_line_values['move_id']
            if key not in dict_invoice_lines_values_by_move_id:
                dict_invoice_lines_values_by_move_id[key] = [invoice_line_values]
            else:
                list_invoice_line_values = dict_invoice_lines_values_by_move_id[key]
                list_invoice_line_values.append(invoice_line_values)
                dict_invoice_lines_values_by_move_id[key] = list_invoice_line_values
        return dict_invoice_lines_values_by_move_id

    def get_free_worker_taxes(self, hour_line, account_id=False):
        # 2023_0116 if there is no account_id provided
        if not account_id:
            product_id = hour_line.x_poule_id.product_id
            account_id = product_id.property_account_expense_id or \
                         product_id.categ_id.property_account_expense_categ_id

        partner_id = hour_line.x_partner_id
        tax_ids = False
        if not partner_id.x_has_vat_on_invoice:
            return tax_ids
        if hour_line.x_poule_id.product_id.id and hour_line.x_poule_id.product_id.supplier_taxes_id:
            tax_ids = hour_line.x_poule_id.product_id.supplier_taxes_id.filtered(
                lambda tax: tax.company_id.id == self.env.company.id)
        elif account_id.tax_ids:
            tax_ids = account_id.tax_ids
        else:
            tax_ids = self.env['account.tax']
        if not tax_ids:
            tax_ids = self.env.company.account_purchase_tax_id
        return tax_ids.ids



