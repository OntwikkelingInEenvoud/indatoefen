from odoo import models, fields


class Level(models.Model):
	_name = "oi1_level"
	_description = "Level"
	_order = 'name'

	name = fields.Char('name', required=True)
	description = fields.Char('description', required=True)
	company_id = fields.Many2one('res.company', string='Company', required=True,
								 default=lambda self: self.env.user.company_id,
								 help="Company related to this level")
	object_id = fields.Selection([('oi1_experience_level', 'Experience level'), ('oi1_language_level', 'Language level') ], string="Object")
