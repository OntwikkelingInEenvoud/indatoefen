from odoo import models, fields, api, _
import datetime, re


class ReportTextType(models.Model):
    _name = "oi1_text.text_type"
    _description = "report text type"

    name = fields.Char("Report text type", translate=True)
    active = fields.Boolean("Active", default=True)

    _sql_constraints = [
        ('oi1_text_text_type_name_uniq',
         'unique (name)',
         'A report text type should be defined only once')
    ]


class ReportText(models.Model):
    _name = "oi1_text.text"
    _description = "Description and report texts"

    def set_default_date_active_from(self):
        return fields.Date.context_today(self, timestamp=datetime.datetime.now())

    @api.model
    def _lang_get(self):
        languages = self.env['res.lang'].search([])
        return [(language.code, language.name) for language in languages]

    name = fields.Char("Description")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    active = fields.Boolean('Active', help="Shows when the tekst should be visible in the report", default=True)
    text = fields.Html('Text', help='Automatically sanitized HTML contents for the text', translate=True, default='')
    date_active_from = fields.Date('Active from date', default=set_default_date_active_from)
    date_active_to = fields.Date('Active to date')
    text_type_id = fields.Many2one('oi1_text.text_type', string='Report text type', required=True)
    partner_id = fields.Many2one('res.partner')

    @api.onchange('active')
    def onchange_active(self):
        if not self.active:
            self.date_active_to = fields.Date.context_today(self, timestamp=datetime.datetime.now())
        if self.active:
            self.date_active_to = None

    def _set_description_from_html(self, values):
        if 'text' in values:
            values['name'] = self._clean_description_from_description_html(values['text'])
        return values

    @staticmethod
    def _clean_description_from_description_html(description_html):
        if not description_html:
            return ""
        description = re.sub(r'<.*?>', '', description_html)
        description = description.replace('&nbsp;', '\t')
        if len(description) > 50:
            description = description[:50]
        return description

    def _set_text_adjustment(self, values, delete=False):
        for oi1_text in self:
            text_type = oi1_text.text_type_id
            if 'text_type_id' in values:
                text_type = self.env['oi1_text.text_type'].browse(values['text_type_id'])
            body = text_type.name
            if 'name' in values:
                body = body + ':\t' + values['name']
            else:
                body = body + ':\t' + oi1_text.name
            if delete:
                body = _("Text deleted") + "\t" + body
            if oi1_text.partner_id.id:
               oi1_text.partner_id.message_post(body=body)
            return body

    def unlink(self):
        self._set_text_adjustment({}, True)
        return super().unlink()

    def write(self, values):
        values = self._set_description_from_html(values)
        self._set_text_adjustment(values)
        res = super().write(values)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals = self._set_description_from_html(vals)
        text_list = super().create(vals_list)
        text_list._set_text_adjustment({})
        return text_list
