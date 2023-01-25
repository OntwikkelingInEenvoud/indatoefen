from odoo import models, fields


class ResPartner(models.Model):
	_inherit = "res.partner"

	oi1_text_ids = fields.One2many('oi1_text.text', 'partner_id')
