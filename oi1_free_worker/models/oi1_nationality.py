from odoo import models, fields, api


class Nationality(models.Model):
	_name = "oi1_nationality"
	_description = "Nationality"
	_order = 'sequence, name'

	_sql_constraints = [
		('oi1_nationality_country_id_uniq',
		 'unique (country_id)',
		 'A country should be defined only once')
	]

	sequence = fields.Integer(string="Sequence", default=0)
	name = fields.Char(string='Description', compute="_compute_name", store=True)
	country_id = fields.Many2one('res.country', required=True, name="Country", help="The country of the nationality. This field is obliged and unique")
	country_code = fields.Char(string="CountryCode", related="country_id.code")
	active = fields.Boolean(string="Active", default=True)
	description = fields.Char(string="Country Des.", translate=True, required=True, help="The description of the nationality")
	schengen_insurance = fields.Boolean(string="Schengen insurance", default=False, help="The free worker from this country could take out a schengen insurance ")

	@api.depends('country_id', 'description')
	def _compute_name(self):
		for nationality in self:
			nationality.name = nationality.country_code + " " + nationality.description
