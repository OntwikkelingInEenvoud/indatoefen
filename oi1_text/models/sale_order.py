from odoo import models, fields, api
import re


class SaleOrder(models.Model):
    _inherit = "sale.order"

    report_quotation_header_text = fields.Html("Report Quoation_header_text",
                                               compute="_compute_report_quotation_header_text")
    report_quotation_footer_text = fields.Html("Report Quoation_footer_text",
                                               compute="_compute_report_quotation_footer_text")
    report_quotation_footer_text_not_html = fields.Char("Report Quoation_footer_text no html",
                                                        compute="_compute_report_quotation_footer_text_no_html")

    report_confirmation_header_text = fields.Html("Report Confirmation header text",
                                                  compute="_compute_report_confirmation_header_text")
    report_confirmation_header_text_not_html = fields.Char("Report Confirmation header text no html",
                                                           compute="_compute_report_confirmation_header_text_no_html")

    report_confirmation_footer_text = fields.Html("Report Confirmation footer text",
                                                  compute="_compute_report_confirmation_footer_text")
    report_confirmation_footer_text_not_html = fields.Char("Report Confirmation footer text no html",
                                                           compute="_compute_report_confirmation_footer_text_no_html")

    report_delivery_terms = fields.Html("Report delivery terms",
                                        compute="_compute_report_delivery_terms_text"
                                        )
    x_customer_contact = fields.Char("Customer contact", compute="_compute_x_customer_contact")
    x_account_tax_ids = fields.Many2one('account.tax', compute="_compute_x_account_tax_ids")
    x_has_one_vat = fields.Boolean('Order has one vat', compute="_compute_x_has_one_vat")
    x_has_delivery_date = fields.Boolean('Order has filled in delivery date', compute="_compute_x_has_delivery_date", default=True)
    x_btw_desc = fields.Char('BTW desc', compute="_compute_x_btw_desc")
    x_btw_perc = fields.Float('BTW Perc', compute="_compute_x_btw_perc")

    def _compute_x_btw_desc(self):
        for so in self:
            btw_desc = ''
            for sol in so.order_line:
                for tax_id in sol.tax_id:
                    btw_desc = tax_id.description
            so.x_btw_desc = btw_desc

    def _compute_x_btw_perc(self):
        for so in self:
            btw_perc = ''
            for sol in so.order_line:
                for tax_id in sol.tax_id:
                    btw_perc = tax_id.amount
            so.x_btw_perc = btw_perc

    def _compute_x_has_delivery_date(self):
        for so in self:
            x_has_delivery_date = False
            for sol in so.order_line:
                if 'x_commitment_date' in self.env['sale.order.line']._fields and sol.x_commitment_date:
                        x_has_delivery_date = True
            if not x_has_delivery_date:
                if 'x_has_delivery_date' in self.env['sale.order']._fields and so.x_has_delivery_date:
                    x_has_delivery_date = True
            so.x_has_delivery_date = x_has_delivery_date

    def _compute_x_has_one_vat(self):
        for so in self:
            has_one_vat = False
            if len(so.x_account_tax_ids) == 1:
                has_one_vat = True
            so.x_has_one_vat = has_one_vat

    def _compute_x_account_tax_ids(self):
        for so in self:
            vat_keys = {}
            vat = list()
            for sale_order_line in so.order_line:
                for tax_id in sale_order_line.tax_id:
                    if tax_id.id not in vat_keys:
                        vat_keys[tax_id.id] = tax_id
                        vat.append(tax_id.id)
            so.x_account_tax_ids = [(6, 0, vat)]

    def _compute_x_customer_contact(self):
        for so in self:
            order_customer_contact = ''
            if 'x_sales_contact_name' in self.env['sale.order']._fields:
                if len(so.x_sales_contact_name) > 0:
                    order_customer_contact = so.x_sales_contact_name
            if order_customer_contact == '':
                if not so.partner_id.is_company:
                    order_customer_contact = so.partner_id.name
            so.x_customer_contact = order_customer_contact

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

    def _compute_report_quotation_header_text(self):
        text_type = self.env.ref('oi1_text.text_type_1')
        for so in self:
            text = False
            texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(texts) > 0:
                text = texts[0]
            if text:
                text = text.text
            so.report_quotation_header_text = text

    def _compute_report_quotation_footer_text(self):
        text_type = self.env.ref('oi1_text.text_type_2')
        for so in self:
            text = False
            texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(texts) > 0:
                text = texts[0]
            if text:
                text = text.text
            so.report_quotation_footer_text = text

    def _compute_report_quotation_footer_text_no_html(self):
        text_type = self.env.ref('oi1_text.text_type_2')
        TAG_RE = re.compile(r'<[^>]+>')
        for so in self:
            text = False
            texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(texts) > 0:
                text = texts[0]
            if text:
                text = TAG_RE.sub(' ', text.text).strip()
            so.report_quotation_footer_text_not_html = text

    def _compute_report_confirmation_header_text(self):
        text_type = self.env.ref('oi1_text.text_type_3')
        for so in self:
            text = False
            texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(texts) > 0:
                text = texts[0]
            if text:
                text = text.text
            so.report_confirmation_header_text = text

    def _compute_report_confirmation_header_text_no_html(self):
        text_type = self.env.ref('oi1_text.text_type_3')
        TAG_RE = re.compile(r'<[^>]+>')
        for so in self:
            text = False
            Texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(Texts) > 0:
                text = Texts[0]
            if text:
                text = TAG_RE.sub(' ', text.text).strip()
            so.report_confirmation_header_text_not_html = text

    def _compute_report_confirmation_footer_text(self):
        text_type = self.env.ref('oi1_text.text_type_4')
        for so in self:
            text = False;
            texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(texts) > 0:
                text = texts[0]
            if text:
                text = text.text
            so.report_confirmation_footer_text = text

    def _compute_report_confirmation_footer_text_no_html(self):
        text_type = self.env.ref('oi1_text.text_type_4')
        TAG_RE = re.compile(r'<[^>]+>')
        for so in self:
            text = False;
            Texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(Texts) > 0:
                text = Texts[0]
            if text:
                text = TAG_RE.sub(' ', text.text).strip()
            so.report_confirmation_footer_text_not_html = text
