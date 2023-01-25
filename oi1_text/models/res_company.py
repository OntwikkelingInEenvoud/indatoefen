from odoo import models, fields, api
import re


class ResCompany(models.Model):
    _inherit = "res.company"

    x_company_slogan_not_html = fields.Char(string="Company slogan", compute="_compute_company_slogan")
    x_delivery_partner_id = fields.Many2one("res.partner", compute="_compute_x_delivery_partner_id")
    x_default_sales_bankId = fields.Many2one('res.partner.bank', string='Default Bank for sales invoices')
    x_default_pur_bank_id = fields.Many2one('res.partner.bank', string='Default Bank for purchase invoices')

    @api.depends('partner_id.child_ids')
    def _compute_x_delivery_partner_id(self):
        for company in self:
            delivery_partner_id = company.partner_id
            delivery_partner_ids = self.env['res.partner'].search([('parent_id', '=', delivery_partner_id.id),
                                                                   ('type', '=', 'delivery')
                                                                   ], limit=1)
            if len(delivery_partner_ids) > 0:
                delivery_partner_id = delivery_partner_ids[0]
            company.x_delivery_partner_id = delivery_partner_id

    def _compute_company_slogan(self):
        text_type = self.env.ref('oi1_text.text_type_16')
        tag_re = re.compile(r'<[^>]+>')
        for company in self:
            text = False
            texts = self.env['oi1_text.text'].search([('text_type_id', '=', text_type.id)])
            if len(texts) > 0:
                text = texts[0]
            if text:
                text = tag_re.sub(' ', text.text).strip()
            company.x_company_slogan_not_html = text
