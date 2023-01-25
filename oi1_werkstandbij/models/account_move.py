from odoo import models, fields, api, exceptions, Command,  _
import datetime
import base64


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    x_sale_invoice_analytic_line_count = fields.Integer(compute='compute_x_sale_invoice_analytic_line_count')
    x_pur_invoice_analytic_line_count = fields.Integer(compute='compute_x_pur_invoice_analytic_line_count')
    x_account_analytic_line_ids = fields.One2many('account.analytic.line', 'x_pur_invoice_id',
                                                  string="Purchase invoices",
                                                  help="Purchase hourlines related to a purchase invoice",
                                                  )
    x_partner_year_amount = fields.Monetary(string="Year amount", compute="_compute_x_partner_year_amount")
    x_no_work_invoice_line_ids = fields.One2many('account.move.line', compute="_compute_x_no_work_invoice_line_ids")
    x_sale_account_analytic_line_ids = fields.One2many('account.analytic.line',
                                                       'x_sale_invoice_id',
                                                       string="Sales hourlines",
                                                       help="Sale hourlines related to a sales invoice")
    x_poule_ids = fields.One2many('oi1_freeworkerpoule', compute="_compute_x_poule_ids")
    x_is_freeworker_visible = fields.Boolean(related="partner_id.x_is_freeworker_visible")
    x_bank_id = fields.Many2one('res.bank', related="partner_bank_id.bank_id")
    x_is_booked_hour_invoice = fields.Boolean(string="Invoice on booked hours",
                                              compute="_compute_x_is_booked_hour_invoice")
    x_is_print_partner_specification_visible = fields.Boolean("Print Specification visible",
                                                              compute="_compute_x_is_print_partner_specification_visible")
    x_is_invoice_refund_visible = fields.Boolean(string="Refund Payment visible",
                                                 compute="_compute_x_is_invoice_refund_visible")
    x_sale_partner_id = fields.Many2one('res.partner', string="Sales partner of the order",
                                        compute="_compute_x_sale_partner_id", store=True, readonly=False)
    x_sale_id = fields.Many2one('sale.order', compute="_compute_x_sale_id", store=True, string="Sale order")
    x_factoring_export_id = fields.Many2one('oi1_werkstandbij.factoring_export', string="Export file")
    state = fields.Selection(selection_add=[('Start_Factoring', 'Ready for factoring'), ('Factored', 'Factored')],
                             ondelete={'Start_Factoring': lambda recs: recs.write({'state': 'posted'}),
                                       'Factored': lambda recs: recs.write({'state': 'posted'}),
                                                                                 })

    def action_post(self):
        action_moves_with_out_invoice_date = self.filtered(lambda l: not l.invoice_date)
        action_moves_with_out_invoice_date.write({'invoice_date': datetime.date.today()})
        return super().action_post()

    def action_reverse(self):

        invoice_refund_hour_wizard_obj = self.env['oi1_werkstandbij.invoice_refund_hour_wizard']
        for account_move in self:
            refund_invoices = self.env['account.move'].sudo().search([('invoice_origin', '=', account_move.name),
                                                                      ('company_id', '=', account_move.company_id.id),
                                                                      ('move_type', '=', 'out_refund')
                                                                      ])
            if len(refund_invoices) > 0:
                raise exceptions.UserError(_("Invoice %s has already refunded with invoice %s" %
                                             (account_move.name, refund_invoices[0].name)))
            if account_move.x_is_booked_hour_invoice:
                action = self.env.ref('oi1_werkstandbij.oi1_invoice_refund_hour_wizard_action').read()[0]
                return action
                invoice_refund_hour_wizard = invoice_refund_hour_wizard_obj.create({})
                invoice_refund_hour_wizard.invoice_id = account_move.id
                invoice_refund_hour_wizard.do_refund_hour_invoice()
                return
        return super().action_reverse()

    @api.depends('invoice_line_ids.x_sale_id', 'state')
    def _compute_x_sale_id(self):
        for account_move in self:
            sale_id = False
            for invoice_line in account_move.invoice_line_ids:
                if invoice_line.x_sale_id and not sale_id:
                    sale_id = invoice_line.x_sale_id
            account_move.x_sale_id = sale_id

    @api.depends('invoice_line_ids.x_sale_id', 'state')
    def _compute_x_sale_partner_id(self):
        for account_move in self:
            x_sale_partner_id = False
            if account_move.x_sale_id.id:
                x_sale_partner_id = account_move.x_sale_id.x_sale_partner_id
            if not x_sale_partner_id:
                x_sale_partner_id = account_move.company_id.partner_id
            if account_move.x_sale_partner_id.id and account_move.state not in ('draft'):
                continue
            account_move.x_sale_partner_id = x_sale_partner_id

    def action_switch_invoice_into_refund_credit_note(self):
        # 2021_0311 Do not allow a credit invoice on hour bookings
        # 2021_1121 Allow credits because the hours are also
        #           negative calculated and make sure the partner banking account is filled in
        self.ensure_one()
        for account_move in self:
            hour_lines = account_move.x_sale_account_analytic_line_ids
            result = super().action_switch_invoice_into_refund_credit_note()
            account_move.x_sale_account_analytic_line_ids = hour_lines

            if account_move.x_hour_invoice:
                bank_statement_line_obj = self.env['account.bank.statement.line']
                bank_statement_lines = bank_statement_line_obj.sudo().search(
                    [('partner_id', '=', account_move.partner_id.id), ('bank_account_id', '!=', False)],
                    order='date', limit=1)
                if len(bank_statement_lines) == 1:
                    account_move.sudo().write({'invoice_partner_bank_id': bank_statement_lines.bank_account_id.id})
            return result

    def set_bank_account_from_free_worker(self):
        account_moves = self.filtered(lambda l: l.x_is_freeworker_visible and not l.partner_bank_id)
        for account_move in account_moves:
            partner_bank_ids = account_move.partner_id.commercial_partner_id.bank_ids
            if len(partner_bank_ids) > 0:
                partner_bank_id = partner_bank_ids[0]
                account_move.partner_bank_id = partner_bank_id
                account_move.x_bank_id = partner_bank_id.bank_id
        return self.mapped('partner_bank_id')

    @api.depends('state', 'move_type')
    def _compute_x_is_invoice_refund_visible(self):
        for account in self:
            if account.move_type in ['in_refund', 'out_refund']:
                account.x_is_invoice_refund_visible = False
            if account.state in ['posted']:
                account.x_is_invoice_refund_visible = True
            else:
                account.x_is_invoice_refund_visible = False

    @api.depends('state', 'x_pur_invoice_analytic_line_count')
    def _compute_x_is_print_partner_specification_visible(self):
        for account_move in self:
            if account_move.x_pur_invoice_analytic_line_count == 0:
                account_move.x_is_print_partner_specification_visible = False
                continue
            if account_move.state == 'draft' or account_move.state == 'cancel':
                account_move.x_is_print_partner_specification_visible = False
            else:
                account_move.x_is_print_partner_specification_visible = True

    @api.depends('x_sale_invoice_analytic_line_count', 'x_sale_invoice_analytic_line_count')
    def _compute_x_is_booked_hour_invoice(self):
        for account in self:
            if account.x_pur_invoice_analytic_line_count > 0 or account.x_sale_invoice_analytic_line_count > 0:
                account.x_is_booked_hour_invoice = True
            else:
                account.x_is_booked_hour_invoice = False

    def _get_invoice_report_as_attachement(self):
        self.ensure_one()
        att_obj = self.env['ir.attachment']
        ir_actions_report = self.env['ir.actions.report']
        report_action = self.env.ref('oi1_reporting_werkstandbij.invoice_report')
        pdf = ir_actions_report._render_qweb_pdf(report_action, self.id)
        attachment_data = {
            'name': report_action.name + " " + self.name + ".pdf",
            'datas': base64.encodebytes(pdf[0]),  # your object Data
            'type': "binary",
            'res_model': 'account.move',
            'res_name': self.name,
            'res_id': self.id,
            'index_content': 'application'
        }
        return att_obj.create(attachment_data)

    def action_invoice_sent(self):
        self.ensure_one()
        att_obj = self.env['ir.attachment']
        attachment_ids = [self._get_invoice_report_as_attachement().id]
        ir_actions_report = self.env['ir.actions.report']

        if len(self.x_sale_account_analytic_line_ids) > 0:
            report_action = self.env.ref('oi1_reporting_werkstandbij.invoice_hours_workers_specification_report')
            content, _content_type = ir_actions_report._render_qweb_pdf(report_action, self.id)
            attachment_data = {
                'name': report_action.name + " " + self.name + ".pdf",
                'datas': base64.encodebytes(content),  # your object Data
                'type': "binary",
                'res_model': 'account.move',
                'res_name': self.name,
                'res_id': self.id,
                'index_content': 'application'
            }
            attachment_ids.append(att_obj.create(attachment_data).id)

        template = self.env.ref('account.email_template_edi_invoice', False)
        if self.move_type in ('in_invoice'):
            template = self.env.ref('oi1_werkstandbij.purchase_account_move_template_email', False)

        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            default_attachment_ids=attachment_ids,
            mark_invoice_as_sent=True,

        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.depends('x_sale_account_analytic_line_ids')
    def _compute_x_poule_ids(self):
        for invoice in self:
            invoice.x_poule_ids = invoice.x_sale_account_analytic_line_ids.mapped("x_poule_id")

    @api.depends('invoice_line_ids')
    def _compute_x_no_work_invoice_line_ids(self):
        for invoice in self:
            invoice.x_no_work_invoice_line_ids = invoice.invoice_line_ids.\
                filtered(lambda l: len(l.x_sales_analytic_account_line_ids) ==0)

    @api.depends('amount_total', 'invoice_date', 'partner_id', 'state')
    def _compute_x_partner_year_amount(self):
        for invoice in self:
            partner_year_amount = 0
            start_date = datetime.datetime(datetime.datetime.now().year, 1, 1)
            end_date = datetime.datetime(datetime.datetime.now().year, 12, 31)
            if invoice.invoice_date:
                start_date = datetime.datetime(invoice.invoice_date.year, 1, 1)
                end_date = datetime.datetime(invoice.invoice_date.year, 12, 31)
            year_invoices = self.env['account.move'].search([('partner_id', '=', invoice.partner_id.id),
                                                             ('invoice_date', '>=', start_date),
                                                             ('invoice_date', '<=', end_date),
                                                             ('move_type', 'in', ('in_invoice', 'in_refund')),
                                                             ])
            for year_invoice in year_invoices.filtered(lambda l: l.state == 'posted'):
                partner_year_amount += year_invoice.amount_total
            invoice.x_partner_year_amount = round(partner_year_amount, 2)

    def action_view_open_invoice_sale_hours(self):
        self.ensure_one()
        action = self.env.ref('hr_timesheet.act_hr_timesheet_line').read()[0]
        invoice_line_ids = []
        for invoice_line in self.invoice_line_ids:
            invoice_line_ids.append(invoice_line.id)
        action['domain'] = [('x_sale_invoice_line_id', 'in', invoice_line_ids)]
        action['views'] = [(self.env.ref('oi1_werkstandbij.view_account_analytic_line_tree').id, 'tree')]
        return action

    def do_print_freeworker_specification(self):
        return self.env.ref('oi1_reporting_werkstandbij.free_workers_specification_report').report_action(self)

    @api.model
    def get_attachments_ids_mail_freeworker_specification(self, account):
        att_obj = self.env['ir.attachment']
        ir_actions_report = self.env['ir.actions.report']

        self.ensure_one()
        attachment_ids = []
        report_action = self.env.ref('oi1_reporting_werkstandbij.free_workers_specification_report')
        pdf = ir_actions_report._render_qweb_pdf(report_action, account.id)
        attachment_data = {
            'name': report_action.name + " " + self.name + ".pdf",
            'datas': base64.encodebytes(pdf[0]),  # your object Data
            'type': "binary",
            'res_model': 'account.move',
            'res_name': self.name,
            'res_id': self.id,
            'index_content': 'application'}
        attachment_ids.append(att_obj.create(attachment_data).id)

        if account.partner_id.x_has_vat_on_invoice:
            report_action = self.env.ref('oi1_reporting_werkstandbij.invoice_report')
            pdf = ir_actions_report._render_qweb_pdf(report_action, account.id)
            attachment_data = {
                'name': report_action.name + " " + account.name + ".pdf",
                'datas': base64.encodebytes(pdf[0]),  # your object Data
                'type': "binary",
                'res_model': 'account.move',
                'res_name': self.name,
                'res_id': self.id,
                'index_content': 'application'
            }
            attachment_ids.append(att_obj.create(attachment_data).id)
        return attachment_ids

    def do_email_freeworker_specification(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        if not self.partner_id.x_communication_email or len(self.partner_id.x_communication_email.strip()) == 0:
            raise exceptions.UserError(_("There is no email filled in for partner %s " % self.partner_id.name))

        template = self.env.ref('oi1_werkstandbij.freeworkerpayment_template_email')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        attachment_ids = self.get_attachments_ids_mail_freeworker_specification(self)
        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            default_attachment_ids=attachment_ids,
        )
        return {
            'name': 'Compose Email',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.depends('invoice_origin')
    def compute_x_sale_invoice_analytic_line_count(self):
        for account_move in self:
            sale_invoice_analytic_line_count = 0
            if account_move.id:
                sale_invoice_analytic_line_count = self.env['account.analytic.line'].sudo().search_count(
                    [('x_sale_invoice_id', '=', account_move.id)])
            account_move.x_sale_invoice_analytic_line_count = sale_invoice_analytic_line_count

    @api.depends('x_account_analytic_line_ids')
    def compute_x_pur_invoice_analytic_line_count(self):
        for invoice in self:
            invoice.x_pur_invoice_analytic_line_count = len(invoice.x_account_analytic_line_ids)

    def set_surcharge_invoiceLine(self):
        invoice_line_obj = self.env['account.move.line']
        surcharge_product_id = self.env.ref('oi1_werkstandbij.invoice_surcharge_product')
        for invoice in self.filtered(lambda l: l.move_type in ('out_invoice', 'out_refund')):
            # Surcharges only calculates to invoices to customers
            invoice_line = False
            group_products = invoice.invoice_line_ids.mapped(
                'x_sales_analytic_account_line_ids.x_poule_id.product_id')
            if len(group_products) == 0:
                continue
            group_product = group_products[0]
            invoice_surcharge_lines = invoice.invoice_line_ids.filtered(
                lambda r: r.product_id.id == surcharge_product_id.id)
            if len(invoice_surcharge_lines) > 0:
                invoice_line = invoice_surcharge_lines[0]
            if not invoice_line and invoice.move_type == 'out_invoice':
                invoice_line = invoice_line_obj.create_account_invoice_move_line_from_product(invoice,
                                                                                              surcharge_product_id)
                sale_order_lines = invoice.invoice_line_ids.mapped('sale_line_ids')
                if len(sale_order_lines) > 0:
                    invoice_line.write({'sale_line_ids': [(4, sale_order_lines[0].id)]})
            worker_invoice_lines = invoice.invoice_line_ids.filtered(lambda r: r.product_id.id == group_product.id)
            quantity = 0.0
            surcharge = 0.0

            for worker_invoice_line in worker_invoice_lines:
                surcharge += worker_invoice_line.x_surcharge_amount
                quantity += worker_invoice_line.quantity
            has_surcharge_invoice_lines = invoice.invoice_line_ids.sale_line_ids.filtered(
                lambda l: l.x_surcharge_amount_visible)
            # 20200226 When the surcharge is calculated by surcharge_amounts then the quantity should be 1
            # because the different values per line
            if len(has_surcharge_invoice_lines) > 0:
                quantity = 1
            # 20210210 If the quantity is zero then the surcharge invoice line should be deleted because there is
            # nothing delivered otherwise a division by zero will occur.
            if quantity == 0:
                quantity = 1
                surcharge = 0.0
            price_unit = surcharge / quantity
            if invoice_line.quantity != quantity or invoice_line.price_unit != price_unit:
                invoice.write({'line_ids': [Command.update(invoice_line.id, {'quantity': quantity, 'price_unit': price_unit, 'sequence': 9999})]})


    def unlink(self):
        result = super().unlink()
        aal_obj = self.env['account.analytic.line']
        aal_obj.check_invoiced()
        return result

    def write(self, values):
        result = super().write(values)
        if result and 'sent' in values:
            for account_invoice in self:
                if account_invoice.sudo().x_wsb_account_invoice.id:
                    account_invoice.sudo().x_wsb_account_invoice.write({'sent': values['sent']})
        return result
