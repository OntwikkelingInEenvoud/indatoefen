from odoo import models, fields, api, exceptions
import re, logging

_logger = logging.getLogger(__name__)

class Invoice(models.Model):
    _inherit = "account.move"

    report_delivery_terms = fields.Html("Report delivery terms",
                                        compute="_compute_report_delivery_terms_text"
                                        )
    order_reference = fields.Char(string="Order reference", compute="_compute_order_reference")
    order_user_names = fields.Char(string="Sellers", compute="_compute_order_user_names")
    order_names = fields.Char(string="Orders", compute="_compute_order_names")
    report_header_text_not_html = fields.Char("Report header_text", compute="_compute_report_header_text_not_html")
    report_footer_text_not_html = fields.Char("Report footer text", compute="_compute_report_footer_text_not_html")
    is_vat_visible = fields.Boolean(string="Is Vat visible", compute="_compute_vat_visible")
    x_order_ids = fields.One2many('sale.order', compute="_compute_related_sale_order")
    order_customer_contact = fields.Char("order customer contact", compute="_compute_order_customer_contact")
    company_slogan_not_html = fields.Char(string="Company slogan", compute="_compute_company_slogan")
    x_is_one_order = fields.Boolean(string="Is one order?", compute="_compute_x_is_one_order")
    x_report_delivery_term_text = fields.Many2one('oi1_text.text', compute="_compute_report_delivery_terms_text")
    x_report_delivery_term_text_short = fields.Many2one('oi1_text.text',
                                                        compute="_compute_report_delivery_terms_text_short")
    x_weight = fields.Float(string="Weight", compute="_compute_x_weight")
    x_is_vendor_invoice = fields.Boolean(string="Vendor Invoice?", compute="_compute_x_is_vendor_invoice")

    @api.depends('invoice_line_ids')
    def _compute_related_sale_order(self):
        for invoice in self:
            invoice.x_order_ids = False
            order_keys = {}
            for invoice_line in invoice.invoice_line_ids:
                for sale_line in invoice_line.sale_line_ids:
                    if sale_line.order_id.id not in order_keys.keys():
                        order_keys[sale_line.order_id.id] = sale_line.order_id
                        invoice.x_order_ids = invoice.x_order_ids + sale_line.order_id

    @api.depends('move_type')
    def _compute_x_is_vendor_invoice(self):
        for invoice in self:
            vendor_invoice = False
            if invoice.move_type in ('in_refund', 'in_invoice'):
                vendor_invoice = True
            invoice.x_is_vendor_invoice = vendor_invoice

    @api.depends('state')
    def _compute_x_weight(self):
        for invoice in self:
            weight = 0.0
            for invoice_line in invoice.invoice_line_ids:
                weight = weight + (invoice_line.quantity * invoice_line.product_id.weight)
            invoice.x_weight = weight

    def get_related_sale_orders(self):
        self.ensure_one()
        return self.invoice_line_ids.sale_line_ids.mapped("order_id")

    @api.depends('company_id', 'partner_id', 'partner_id.lang')
    def _compute_report_delivery_terms_text(self):
        text_type = self.env.ref('oi1_text.text_type_11')
        for so in self:
            text = False
            texts = self.env['oi1_text.text'].with_context({'lang': so.partner_id.lang}).search(
                [('text_type_id', '=', text_type.id),
                 ('company_id', '=', so.company_id.id)])
            if len(texts) > 0:
                text = texts[0]
            if not text:
                texts = self.env['oi1_text.text'].with_context({'lang': so.partner_id.lang}).search(
                    [('text_type_id', '=', text_type.id)])
                if len(texts) > 0:
                    text = texts[0]
            if text:
                text = text.with_context({'lang': so.partner_id.lang}).text
            so.x_report_delivery_term_text = text

    @api.depends('company_id', 'partner_id', 'partner_id.lang')
    def _compute_report_delivery_terms_text_short(self):
        text_type = self.env.ref('oi1_text.text_type_17')
        for so in self:
            text = False
            texts = self.env['oi1_text.text'].with_context({'lang': so.partner_id.lang}).search(
                [('text_type_id', '=', text_type.id),
                 ('company_id', '=', so.company_id.id)])
            if len(texts) > 0:
                text = texts[0]
            if not text:
                texts = self.env['oi1_text.text'].with_context({'lang': so.partner_id.lang}).search(
                    [('text_type_id', '=', text_type.id)])
                if len(texts) > 0:
                    text = texts[0]
            so.x_report_delivery_term_text_short = text

    def _compute_order_names(self):
        for invoice in self:
            order_names = ''
            for order_id in invoice.get_related_sale_orders():
                if len(order_names) != 0:
                    order_names = order_names + ", "
                order_names = order_names + order_id.name
            invoice.order_names = order_names

    def _compute_x_is_one_order(self):
        for invoice in self:
            if len(invoice.get_related_sale_orders()) == 1:
                invoice.x_is_one_order = True
            else:
                invoice.x_is_one_order = False

    def _compute_company_slogan(self):
        text_type = self.env.ref('oi1_text.text_type_16')
        tag_re = re.compile(r'<[^>]+>')
        for invoice in self:
            text = False
            texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(texts) > 0:
                text = texts[0]
            if text:
                text = tag_re.sub(' ', text.text).strip()
            invoice.company_slogan_not_html = text

    def _compute_order_customer_contact(self):
        for invoice in self:
            order_customer_contact = ''
            for order in invoice.get_related_sale_orders():
                if 'x_sales_contact_name' in self.env['sale.order']._fields:
                    if len(order.x_sales_contact_name) > 0:
                        order_customer_contact = order.x_sales_contact_name
                if order_customer_contact == '':
                    if not order.partner_id.is_company:
                        order_customer_contact = order.partner_id.name
            invoice.order_customer_contact = order_customer_contact

    @api.depends('fiscal_position_id', 'partner_id.vat')
    def _compute_vat_visible(self):
        for invoice in self:
            if invoice.partner_id.vat and len(invoice.partner_id.vat.strip()) > 0:
                invoice.is_vat_visible = True
                continue
            try:
                fiscal_position = self.env.ref('l10n_nl.fiscal_position_template_national')
                if not invoice.fiscal_position_id.id or invoice.fiscal_position_id.id == fiscal_position.id:
                    invoice.is_vat_visible = False
                    continue
            except ValueError:
                _logger.warning("Module l10n_nl not installed")
            invoice.is_vat_visible = True

    @api.depends('company_id')
    def _compute_report_delivery_terms_text(self):
        text_type = self.env.ref('oi1_text.text_type_11')
        for so in self:
            text = False
            texts = self.env['oi1_text.text'].with_context({'lang': so.partner_id.lang}).search(
                [('text_type_id', '=', text_type.id),
                 ('company_id', '=', so.company_id.id)])
            if len(texts) > 0:
                text = texts[0]
            if not text:
                texts = self.env['oi1_text.text'].with_context({'lang': so.partner_id.lang}).search(
                    [('text_type_id', '=', text_type.id)])
                if len(texts) > 0:
                    text = texts[0]
            if text:
                text = text.text
            so.report_delivery_terms = text

    def _compute_order_user_names(self):
        for invoice in self:
            order_user_names = ''
            for order_id in invoice.get_related_sale_orders():
                if len(order_user_names) > 0:
                    order_user_names += ', '
                order_user_names = order_id.user_id.name
            invoice.order_user_names = order_user_names

    def _compute_order_reference(self):
        for invoice in self:
            reference = ''
            for order in invoice.get_related_sale_orders():
                if order.client_order_ref:
                    if len(reference) > 0:
                        reference = reference + ', '
                    reference = reference + order.client_order_ref
            invoice.order_reference = reference

    def _compute_report_header_text_not_html(self):
        text_type = self.env.ref('oi1_text.text_type_14')
        tag_re = re.compile(r'<[^>]+>')
        for invoice in self:
            text = False
            texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(texts) > 0:
                text = texts[0]
            if text:
                text = tag_re.sub(' ', text.text).strip()
            invoice.report_header_text_not_html = text

    def _compute_report_footer_text_not_html(self):
        text_type = self.env.ref('oi1_text.text_type_15')
        tag_re = re.compile(r'<[^>]+>')
        for invoice in self:
            text = False
            texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(texts) > 0:
                text = texts[0]
            if text:
                text = tag_re.sub(' ', text.text).strip()
            invoice.report_footer_text_not_html = text

