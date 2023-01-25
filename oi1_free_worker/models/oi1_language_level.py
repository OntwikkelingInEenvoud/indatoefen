from odoo import models, fields, api


class LanguageLevel(models.Model):
	_name = "oi1_language_level"
	_description = "Language level"
	_order = 'sequence, name'

	@api.model
	def _get_languages(self):
		return self.env['res.lang'].get_available()

	sequence = fields.Integer('Sequence', default=99)
	name = fields.Char('Name', compute="adjust_name", default='', store=True)
	lang = fields.Selection(_get_languages, string='Language', required=True)
	level_id = fields.Many2one('oi1_level', string="Level", required=True,
							   domain=[('object_id', '=', 'oi1_language_level')])

	partner_ids = fields.Many2many('res.partner', string='Freeworkers')
	freeworker_poule_ids = fields.Many2many('oi1_freeworkerpoule', string="Poules")
	company_id = fields.Many2one('res.company', string='Company', required=True,
								 default=lambda self: self.env.user.company_id,
								 help="Company related to this experience level")

	@api.depends('lang', 'level_id')
	def adjust_name(self):
		for language_level in self:
			name = ''
			if language_level.lang:
				selections = dict(self._get_languages())
				key_list = list(selections.keys())
				val_list = list(selections.values())
				name = val_list[key_list.index(language_level.lang)]
			if language_level.level_id.id:
				name = name + "." + language_level.level_id.description
			language_level.name = name
