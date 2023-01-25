from odoo import models, fields, api


class ExperienceLevel(models.Model):
	_name = "oi1_experience_level"
	_description = "Experience level"
	_order = 'experience_id, level_id'

	@api.depends('experience_id', 'level_id')
	def adjust_name(self):
		for experience_level in self:
			name = ''
			if experience_level.experience_id:
				name = experience_level.experience_id.name
			if experience_level.level_id:
				name = name + "." + experience_level.level_id.name
			experience_level.name = name

	name = fields.Char('Name', compute="adjust_name", store=True)
	experience_id = fields.Many2one('oi1_experience', required=True)
	experience_name = fields.Char(related='experience_id.name')
	level_id = fields.Many2one('oi1_level', required=True, domain=[('object_id', '=', 'oi1_experience_level')])

	partner_ids = fields.Many2many('res.partner', string='Freeworkers')
	freeworker_poule_ids = fields.Many2many('oi1_freeworkerpoule', string="Poules")
	company_id = fields.Many2one('res.company', string='Company', required=True,
								 default=lambda self: self.env.user.company_id,
								 help="Company related to this experience level")
