from odoo import models, fields


class Education(models.Model):
	_name = "oi1_education"
	_description = "Education"

	name = fields.Char('name')
	description = fields.Char('description')

	x_partner_ids = fields.Many2many('res.partner', string='Freeworkers')
	x_company_id = fields.Many2one('res.company', string='Company', required=True,
								   default=lambda self: self.env.user.company_id,
								   help="Company related to this education")
