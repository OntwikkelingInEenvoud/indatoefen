from odoo import api, fields, models, exceptions, Command, _


class InvoiceWizard(models.TransientModel):
    _name = "oi1_werkstandbij.invoice_wizard"
    _description = "Create invoices"

    @api.model
    def get_sales_journal(self):
        journal = False
        journals = self.env['account.journal'].sudo().search([('type', '=', 'sale')])
        if len(journals) > 0:
            journal = journals[0]
        if len(journals) == 0:
            raise exceptions.UserError(_(" No sale journal found for company %s.") % self.env.company.id)
        return journal

    @staticmethod
    def check_if_hour_lines_are_ready_for_invoice(hour_lines):
        # Are the lines approved?
        new_lines = hour_lines.filtered(lambda r: r.x_state != 'approved' and r.x_state != 'invoiced')
        if len(new_lines) > 0:
            raise exceptions.UserError(
                _(" Hour line %s is not approved") % new_lines[0].name)
        # Is the a sales order related to the hour line?
        new_lines = hour_lines.filtered(lambda r: not r.x_sale_id.id)
        if len(new_lines) > 0:
            raise exceptions.UserError(
                _(" Hour line %s is not related to an sales order") % new_lines[0].name)
        # Is the line already invoiced?
        new_lines = hour_lines.filtered(lambda r: r.x_sale_invoice_line_id.id and r.x_pur_invoice_line_id.id)
        if len(new_lines) > 0:
            raise exceptions.UserError(
                _(" Hour line %s is already invoiced") % new_lines[0].name)
        # Is the line already invoiced?
        new_lines = hour_lines.filtered(lambda r: not r.project_id.sale_line_id.id)
        if len(new_lines) > 0:
            raise exceptions.UserError(_("A poule should be related to a sales order"))

    def do_create_invoices(self):
        for wizard in self:
            return wizard.create_invoices()

    @api.model
    def create_invoices(self):
        hour_lines = self.env['account.analytic.line'].browse(self._context.get('active_ids', []))
        InvoiceWizard.check_if_hour_lines_are_ready_for_invoice(hour_lines)
        sales_hour_lines = hour_lines.filtered(lambda r: not r.x_sale_invoice_line_id.id)
        hour_lines.with_context(check_move_validity=False).write({'system': 1, 'x_state': 'customer_invoiced'})
        return self.create_customer_invoices(sales_hour_lines)

    @api.model
    def _get_surcharge_invoice_line_dict_values(self, list_invoice_line_values):
        surcharge_product_id = self.env.ref('oi1_werkstandbij.invoice_surcharge_product')
        quantity = 0.0
        surcharge = 0.0
        sale_line_ids = []
        for dict_invoice_line in list_invoice_line_values:
            if dict_invoice_line['product_id'] == surcharge_product_id.id:
                continue
            quantity += dict_invoice_line['quantity']
            surcharge += dict_invoice_line['x_surcharge_amount']
            for add_sale_line_ids in dict_invoice_line['sale_line_ids']:
                sale_line_ids.append(add_sale_line_ids[1])
        list_sale_line = self.env['sale.order.line'].browse(sale_line_ids)
        if len(list_sale_line.filtered(lambda l: l.x_surcharge_amount_visible)) > 0:
            quantity = 1
        if quantity == 0:
            quantity = 1
            surcharge = 0.0
        price_unit = surcharge / quantity
        return {'quantity': quantity,
                'price_unit': price_unit,
                'sequence': 9999,
                'product_id': surcharge_product_id.id}

    @api.model
    def create_customer_invoices(self, hour_lines):
        dict_invoices, list_invoice_line_values = self._get_invoices(hour_lines)
        dict_invoice_lines = self._get_sales_invoice_lines(hour_lines, list_invoice_line_values)
        for order_name in dict_invoices.keys():
            account_move = dict_invoices[order_name]
            account_move.with_context(dynamic_unlink=True).write({'line_ids': False})
            account_move_invoice_line_values = dict_invoice_lines[order_name]
            account_move_invoice_line_values.append \
                (self._get_surcharge_invoice_line_dict_values(account_move_invoice_line_values))
            for invoice_line_values in dict_invoice_lines[order_name]:
                account_move.write({'invoice_line_ids': [Command.create(invoice_line_values)]})
        return list(dict_invoices.values())

    @api.model
    def _add_sales_invoice_to_dict_invoices(self, partner_id, order_number, dict_invoices):
        invoice_obj = self.env['account.move']
        sale_order_obj = self.env['sale.order']
        journal = self.get_sales_journal()
        invoices = invoice_obj.search([('partner_id', '=', partner_id.id),
                                       ('state', '=', 'draft'),
                                       ('move_type', '=', 'out_invoice'),
                                       ('company_id', '=', self.env.company.id),
                                       ('invoice_origin', '=', order_number)
                                       ], limit=1)
        invoice = False
        if len(invoices) == 1:
            invoice = invoices[0]
        if not invoice:
            sale_order = sale_order_obj.search([('name', '=', order_number)])[0]
            payment_term_id = sale_order.payment_term_id
            if not payment_term_id.id:
                raise exceptions.UserError(
                    _(
                        " There is not given a paymentterm to salesorder %s. Please provide one") % sale_order.name)
            fiscal_position_id = self.env['account.fiscal.position']._get_fiscal_position(
                partner_id,
                partner_id)
            invoice = invoice_obj.create({'partner_id': partner_id.id,
                                          'move_type': 'out_invoice',
                                          'journal_id': journal.id,
                                          'fiscal_position_id': fiscal_position_id,
                                          'company_id': self.env.company.id,
                                          'invoice_payment_term_id': payment_term_id.id,
                                          'invoice_origin': order_number,
                                          'partner_bank_id': journal.company_id.x_default_sales_bankId.id,
                                          })
        dict_invoices.update({order_number: invoice[0]})
        return dict_invoices

    @api.model
    def _get_invoices(self, hour_lines):
        tools_obj = self.env['oi1.object_tools']
        dict_invoices = {}
        dict_invoice_lines = []
        if len(hour_lines) == 0:
            return dict_invoices
        for hour_line in hour_lines:
            order_number = hour_line.x_sale_id.name
            partner_id = hour_line.x_sale_id.partner_id
            if order_number not in dict_invoices:
                dict_invoices = self._add_sales_invoice_to_dict_invoices(partner_id, order_number, dict_invoices)
            account_move = dict_invoices[order_number]
            account_move.with_context({'system': 1}).write({'timesheet_ids': [(4, hour_line.id)]})
        for account_move in dict_invoices.values():
            list_invoice_line_values = tools_obj.get_dictionary_values(account_move.invoice_line_ids)
            # 2023_0111 Replace the move_id to the order_number because this is mapped later in the invoices
            for invoice_line_values in list_invoice_line_values:
                invoice_line_values['move_id'] = order_number
                dict_invoice_lines.append(invoice_line_values)
        return dict_invoices, dict_invoice_lines

    @api.model
    def add_taxes(self, hour_line):
        product_id = hour_line.x_poule_id.product_id
        sale_id = hour_line.x_sale_id
        taxes = product_id.taxes_id.filtered(
            lambda r: not sale_id.company_id or r.company_id == sale_id.company_id)
        if sale_id.fiscal_position_id and taxes:
            tax_ids = sale_id.fiscal_position_id.map_tax(taxes, product_id, sale_id.partner_id).ids
        else:
            tax_ids = taxes.ids
        return tax_ids

    @api.model
    def _get_sales_invoice_lines(self, hour_lines, list_invoice_lines_values):
        dict_invoice_lines_values_by_move_id = {}
        free_worker_poule_obj = self.env['oi1_freeworkerpoule']
        tools_obj = self.env['oi1.object_tools']
        """
		2021_0629 	Gathers the description on the invoice this will be the name of the main poule if the current 
					poule has a main poule
		"""

        def _get_invoice_name():
            project_name = hour_line.project_id.name
            poules = free_worker_poule_obj.search([('project_id', '=', hour_line.project_id.id)])
            if len(poules) == 1:
                if poules.parent_id.id:
                    project_name = poules.parent_id.name
            return project_name + " " + str_date

        pos = 0
        dict_invoice_lines = {}
        for invoice_line_values in list_invoice_lines_values:
            analytic_account_line_ids = invoice_line_values['x_sales_analytic_account_line_ids']
            analytic_hour_line = False
            key = False
            pos += 1
            if invoice_line_values['product_id'] == self.env.ref('oi1_werkstandbij.invoice_surcharge_product').id:
                continue
            if analytic_account_line_ids:
                analytic_account_line_ids = tools_obj.get_id_list(analytic_account_line_ids)
                if len(analytic_account_line_ids) > 0:
                    analytic_hour_line = self.env['account.analytic.line'].browse([analytic_account_line_ids[0]])
            if analytic_hour_line:
                key = str(analytic_hour_line.x_sale_id.id) + "." + str(analytic_hour_line.project_id.id) + "." + str(
                    analytic_hour_line.date) + "." + str(analytic_hour_line.x_rate)
            if not key:
                key = 'QQQQQQ.' + str(pos)
            dict_invoice_lines[key] = invoice_line_values
        for hour_line in hour_lines:
            key = str(hour_line.x_sale_id.id) + "." + str(hour_line.project_id.id) + "." + str(
                hour_line.date) + "." + str(hour_line.x_rate)
            surcharge_amount = (hour_line.get_sales_tariff() - hour_line.x_rate) * hour_line.unit_amount
            if key in dict_invoice_lines:
                dict_invoice_lines[key]['quantity'] = dict_invoice_lines[key]['quantity'] + hour_line.unit_amount
                dict_invoice_lines[key]['x_surcharge_amount'] = dict_invoice_lines[key][
                                                                    'x_surcharge_amount'] + surcharge_amount
                x_sales_analytic_account_line_ids = dict_invoice_lines[key]['x_sales_analytic_account_line_ids']
                x_sales_analytic_account_line_ids.append((4, hour_line.id))
                dict_invoice_lines[key]['x_sales_analytic_account_line_ids'] = x_sales_analytic_account_line_ids
            if key not in dict_invoice_lines:
                date = fields.Date.from_string(hour_line.date)
                str_date = ("0" + str(date.day))[-2:] + "-" + ("0" + str(date.month))[-2:] + "-" + str(date.year)
                name = _get_invoice_name()
                if hour_line.task_id.id:
                    name = name + ' ' + hour_line.task_id.name
                product = hour_line.x_poule_id.product_id
                if not hour_line.project_id.id:
                    raise exceptions.UserError(_(" Hourline %s has no related project/poule ") % (
                        hour_line.name))
                if not hour_line.x_poule_id.id:
                    raise exceptions.UserError(_(" Hourline %s has no related poule ") % (
                        hour_line))
                if not product.active:
                    raise exceptions.UserError(
                        _(" Product %s is not active. Choose a different product for poule %s") % (
                            product.name, hour_line.x_poule_id.name))
                income_account = product.with_context(
                    with_company=self.env.company.id).property_account_income_id or product.categ_id.with_context(
                    with_company=self.env.company.id).property_account_income_categ_id
                dict_invoice_lines[key] = {'quantity': hour_line.unit_amount,
                                           'price_unit': hour_line.x_rate,
                                           'product_id': product.id,
                                           'account_id': income_account.id,
                                           'name': name,
                                           'x_del_date': hour_line.date,
                                           'x_sale_id': hour_line.x_sale_id.id,
                                           'x_sales_analytic_account_line_ids': [(4, hour_line.id)],
                                           'move_id': hour_line.x_sale_id.name,
                                           'x_surcharge_amount': surcharge_amount,
                                           'display_type': 'product',
                                           'tax_ids': [(6, 0, self.add_taxes(hour_line))],
                                           'sale_line_ids': [(4, hour_line.project_id.sale_line_id.id)],
                                           }
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
