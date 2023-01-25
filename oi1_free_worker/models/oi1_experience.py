from odoo import models, fields


class Experience(models.Model):
	_name = "oi1_experience"
	_description = "Experience"

	name = fields.Char('name')
	description = fields.Char('description')
	company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id,
								 help="Company related to this experience")
