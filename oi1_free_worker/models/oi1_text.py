from odoo import models, api, fields, exceptions, _


class Text(models.Model):
    _inherit = 'oi1_text.text'

    def _set_text_adjustment(self, values, delete=False):
        for oi1_text in self:
            body = super(Text, oi1_text)._set_text_adjustment(values, delete)
            if oi1_text.partner_id.x_is_freeworker:
               oi1_text.partner_id.x_freeworker_id.message_post(body=body)


