from odoo import models, fields


class res_partner_category(models.Model):
	_inherit = 'res.partner.category'
	x_prev_code = fields.Char(string="Former Unique code")

