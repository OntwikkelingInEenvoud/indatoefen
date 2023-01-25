from odoo import models, fields, api, exceptions, _
from datetime import date


class CommissionPayment(models.Model):
    _name = "oi1_sale_commission_payment"
    _description = "Commission payment"
    _inherit = ['mail.thread']

    _sql_constraints = [
        ('oi1_sale_commission_payment_unique_number', 'unique (number)', 'Number already exists')
    ]

    def do_disapprove(self):
        for ComPayMent in self:
            ComPayMent.state = 'disapproved'

    def do_approve(self):
        for commission in self:
            if commission.state == 'invoiced':
                continue
            commission.write({'state': 'approved'})

    def do_invoice(self):
        sale_commissions = self.filtered(lambda l: l.state == 'approved')
        self.create_pur_invoice(sale_commissions)

    def create_pur_invoice(self, commissions):
        for commission in commissions:
            commission_lines = commission.sale_commission_payment_lines. \
                filtered(lambda l: l.type != 'reservation' and not l.pur_invoice_line_id)
            if len(commission_lines) == 0:
                return
            commission_journal_id = self.env.ref('oi1_werkstandbij.commissionpayment_journal').id
            invoice_obj = self.env['account.move']
            invoices = invoice_obj.search([('partner_id', '=', commission.partner_id.id),
                                           ('state', '=', 'draft'),
                                           ('move_type', '=', 'in_invoice'),
                                           ('company_id', '=', self.env.company.id),
                                           ('journal_id', '=', commission_journal_id),
                                           ])
            invoice = False
            if len(invoices) > 0:
                invoice = invoices[0]
            if not invoice:
                invoice_partner_bank_id = commission.partner_id.x_partner_bank_id
                invoice = invoice_obj.create({'partner_id': commission.partner_id.id,
                                              'invoice_date': date.today(),
                                              'move_type': 'in_invoice',
                                              'journal_id': commission_journal_id,
                                              'company_id': self.env.company.id,
                                              'payment_reference': commission.number,
                                              'partner_bank_id': invoice_partner_bank_id
                                              })
                if not self.is_vat_partner_id(invoice.partner_id):
                    body = _("Partner %s is configured for not having btw on the invoice so no btw is calculated"
                             % invoice.partner_id.name)
                    invoice.message_post(body=body)

            for commission_line in commission_lines:
                invoice_line = self._create_update_invoice_lines(commission_line, invoice)
                commission_line.pur_invoice_line_id = invoice_line.id
            if len(commission.sale_commission_payment_lines.filtered(lambda l: not l.pur_invoice_line_id)) == 0:
                commission.write({'state': 'invoiced', 'invoice_id': invoice.id})

    def is_vat_partner_id(self, partner_id):
        if not partner_id.x_has_vat_on_invoice:
            return False
        return True

    def _get_invoice_free_worker_vat(self, invoice_line):
        vat = []
        if not self.is_vat_partner_id(invoice_line.move_id.partner_id):
            return vat
        if not invoice_line.move_id.partner_id.vat or len(invoice_line.move_id.partner_id.vat) ==0:
            raise exceptions.UserError(_('Please provide a valid vat number for partner %s which is needed '
                                         'because there will be vat on the invoice') % invoice_line.move_id.partner_id.name)
        vat = invoice_line._get_computed_taxes()
        return vat

    def _create_update_invoice_lines(self, commission_line, invoice):
        account_move_line_obj = self.env['account.move.line']
        partner_name = ''
        sale_name = ''
        commission_name = ''

        quantity = commission_line.qty
        if commission_line.type == 'payment':
            quantity = -quantity
        if commission_line.sale_id.partner_id.name:
            partner_name = commission_line.sale_id.partner_id.name + " \ "
        if len(partner_name) == 0 and commission_line.partner_worker_id.id:
            partner_name = commission_line.partner_worker_id.name + " \ "
        if commission_line.sale_id.name:
            sale_name = commission_line.sale_id.name + " \ "
        if commission_line.commission_id.name:
            commission_name = commission_line.commission_id.name
        name = partner_name + sale_name + commission_name
        if commission_line.oi1_sale_commission_id.type == 'reservation':
            name = _("Payment of") + ' ' + name + ' ' + commission_line.name
        invoice_line_obj = self.env['account.move.line']
        product = commission_line.commission_id.product_id
        invoice_lines = invoice_line_obj.search([('move_id', '=', invoice.id),
                                                 ('name', '=', name),
                                                 ('price_unit', '=', commission_line.rate)
                                                 ])
        if len(invoice_lines) > 0:
            invoice_line = invoice_lines[0]
            quantity = invoice_line.quantity + quantity
            values = {'quantity': quantity}
            invoice_line.update_account_invoice_move_line(values)
            return invoice_line
        values = {'move_id': invoice.id,
                  'product_id': product.id,
                  'price_unit': commission_line.rate,
                  'quantity': quantity,
                  'account_id': product.property_account_expense_id.id
                                or product.categ_id.property_account_expense_categ_id.id,
                  'name': name,
                  'exclude_from_invoice_tab': False,
                  }
        invoice_line = account_move_line_obj.create_account_invoice_move_line(values)
        invoice_line.update_account_invoice_move_line({'tax_ids': self._get_invoice_free_worker_vat(invoice_line)})
        return invoice_line

    def do_print_commissionreport(self):
        return self.env.ref('oi1_reporting_werkstandbij.commission_payment_report').report_action(self)

    def do_email_commissionreport(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        if not self.partner_id.x_communication_email or len(self.partner_id.x_communication_email.strip()) == 0:
            raise exceptions.UserError(_("There is no emailadres filled in for partner %s " % self.partner_id.name))

        template = self.env.ref('oi1_werkstandbij_commission.commission_template_email')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='oi1_sale_commission_payment',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
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

    def write(self, vals):
        for commission in self:
            if commission.number == False and 'number' not in vals:
                vals['number'] = commission.getNumber()
        res = super(CommissionPayment, self).write(vals)
        return res

    @api.model
    def getNumber(self):
        SequenceObj = self.env['ir.sequence']
        return SequenceObj.next_by_code('oi1_werkstandbij.oi1_sale_commission_payment')

    name = fields.Char('Name', required=True)
    number = fields.Char('Number', default=lambda self: self.getNumber())
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    state = fields.Selection([
        ('concept', 'Ingevoerd'),
        ('disapproved', 'Afgekeurd'),
        ('approved', 'Goedgekeurd'),
        ('invoiced', 'Gefactureerd'),
    ], default='concept', string="Status", tracking=True)
    invoice_id = fields.Many2one('account.move')
    date = fields.Date(default=fields.Date.today())
    amount = fields.Float(string="Amount", compute="cmp_total_payment_amount", store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company,
                                 help="Company related to this commission")
    sale_commission_payment_lines = fields.One2many('oi1_sale_commission_payment_line', 'oi1_sale_commission_id')
    order_ids = fields.One2many('sale.order', compute="_compute_order_ids")
    partner_worker_ids = fields.One2many('res.partner', compute="_compute_partner_worker_ids")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id, store=True)
    payment_company_id = fields.Many2one('res.company', compute="_compute_payment_company")
    payment_invoice_id = fields.Many2one('account.move', string="Payment invoice",
                                         compute="_compute_payment_invoice_id")
    period = fields.Char(string="Period", default=_("Manual"))
    partner_is_freeworker = fields.Boolean(related="partner_id.x_is_freeworker_visible")
    freeworker_id = fields.Many2one(related="partner_id.x_freeworker_id")
    are_action_buttons_visible = fields.Boolean(compute="_compute_are_action_buttons_visible")
    is_do_approve_visible = fields.Boolean(compute="_compute_is_do_approve_visible")
    is_do_disapprove_visible = fields.Boolean(compute="_compute_is_do_disapprove_visible")
    is_do_invoice_visible = fields.Boolean(compute="_compute_is_do_invoice_visible")
    is_do_un_reserve_visible = fields.Boolean(compute="_compute_is_do_un_reserve_visible")
    active = fields.Boolean(string="Active", compute="_compute_active", store=True, default=True)
    type = fields.Selection([('commission', 'Commission'), ('reservation', 'Reservation')],
                            default='commission', string='Type', tracking=True)
    commission_agreement = fields.Text(string="Commission agreement", compute="_compute_commission_agreement")
    commission_contact = fields.Many2one('res.partner', string="Commission contact", compute="_compute_commission_contact")
    communication_email = fields.Char(string="Communication email", compute="_compute_communication_email")

    @staticmethod
    def do_go_to_not_paid_invoice_commission_forms(env):
        commission_journal_id = env.ref('oi1_werkstandbij.commissionpayment_journal').id
        return {
            'name': _("Not paid Commission Bills"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'views': [
                [env.ref('account.view_invoice_tree').id, 'tree'],
                [env.ref('account.view_move_form').id, 'form'],
                ],
            'search_view_id': env.ref('account.view_account_invoice_filter').id,
            'domain': [('move_type', '=', 'in_invoice'),
                       ('journal_id', '=', commission_journal_id),
                       ('state', '!=', 'cancel'),
                       ('invoice_payment_state', '!=', 'paid')],
            'context': {'default_type': 'in_invoice'}
        }

    @api.depends("commission_contact")
    def _compute_communication_email(self):
        for sale_commission in self:
            sale_commission.communication_email = sale_commission.commission_contact.email

    def _compute_is_do_un_reserve_visible(self):
        for sale_commission in self:
            is_do_un_reserve_visible = False
            if sale_commission.state == 'approved' and sale_commission.type == 'reservation':
                is_do_un_reserve_visible = True
            sale_commission.is_do_un_reserve_visible = is_do_un_reserve_visible


    def _compute_commission_contact(self):
        for sale_commission in self:
            commission_contact = sale_commission.partner_id
            if sale_commission.partner_id.x_is_freeworker and sale_commission.partner_id.x_freeworker_id.communication_partner_id.id:
                commission_contact  = sale_commission.partner_id.x_freeworker_id.communication_partner_id
            sale_commission.commission_contact = commission_contact

    def _compute_commission_agreement(self):
        for commission_payment in self:
            commission_agreement = False
            if commission_payment.partner_id.id:
                commission_text_type_id = self.env.ref('oi1_werkstandbij_commission.text_commission_type').id
                commission_agreements = commission_payment.partner_id.oi1_text_ids.\
                    filtered(lambda l: l.text_type_id.id == commission_text_type_id)
            if len(commission_agreements) > 0:
                commission_agreement = commission_agreements[0].name
            commission_payment.commission_agreement = commission_agreement

    @api.depends('state')
    def _compute_is_do_invoice_visible(self):
        for sale_commission in self:
            is_do_invoice_visible = False
            if sale_commission.state == 'approved' and sale_commission.type == 'commission':
                is_do_invoice_visible = True
            sale_commission.is_do_invoice_visible = is_do_invoice_visible

    @api.depends('state')
    def _compute_active(self):
        for sale_commission_payment in self:
            active = True
            if sale_commission_payment.state in ['disapproved']:
                active = False
            sale_commission_payment.active = active

    @api.depends('company_id', 'state')
    def _compute_is_do_disapprove_visible(self):
        for payment in self:
            if not payment.are_action_buttons_visible:
                payment.is_do_disapprove_visible = False
                continue
            if payment.state in ('concept', 'approved'):
                payment.is_do_disapprove_visible = True
                continue
            payment.is_do_disapprove_visible = False

    @api.depends('company_id', 'state')
    def _compute_is_do_approve_visible(self):
        for payment in self:
            if not payment.are_action_buttons_visible:
                payment.is_do_approve_visible = False
                continue
            if payment.state in ('concept', 'disapproved'):
                payment.is_do_approve_visible = True
                continue
            payment.is_do_approve_visible = False

    @api.depends('company_id')
    def _compute_are_action_buttons_visible(self):
        for payment in self:
            if self.company_id == self.env.company:
                payment.are_action_buttons_visible = True
            else:
                payment.are_action_buttons_visible = False

    @api.depends('sale_commission_payment_lines.partner_worker_id')
    def _compute_partner_worker_ids(self):
        for commission in self:
            commission.partner_worker_ids = commission.sale_commission_payment_lines.filtered(
                lambda l: not l.sale_id.id). \
                mapped("partner_worker_id")

    @api.depends('invoice_id.state')
    def _compute_payment_invoice_id(self):
        account_invoice_obj = self.env['account.move']
        for commission in self:
            payment_invoice = False
            if commission.invoice_id.id:
                payment_invoice = commission.invoice_id
                name = commission.invoice_id.name
                wsb_company_id = payment_invoice.company_id.x_payment_company_id
                accounts = account_invoice_obj.sudo().search([('company_id', '=', wsb_company_id.id),
                                                              ('invoice_origin', '=', name)
                                                              ])
                if len(accounts) > 0:
                    payment_invoice = accounts[0]
            commission.payment_invoice_id = payment_invoice

    @api.depends('invoice_id.state')
    def _compute_payment_company(self):
        for commission in self:
            payment_company_id = commission.company_id
            invoice = commission.payment_invoice_id
            if invoice:
                payment_company_id = invoice.sudo().company_id
            commission.payment_company_id = payment_company_id

    @api.depends('sale_commission_payment_lines.sale_id')
    def _compute_order_ids(self):
        for commission in self:
            commission.order_ids = commission.sale_commission_payment_lines.mapped("sale_id")

    @api.depends('sale_commission_payment_lines.amount')
    def cmp_total_payment_amount(self):
        for com_payment in self:
            amount = 0.0
            for com_payment_line in com_payment.sale_commission_payment_lines:
                amount += com_payment_line.amount
            com_payment.amount = amount
