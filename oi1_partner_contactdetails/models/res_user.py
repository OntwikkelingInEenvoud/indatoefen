from odoo import models, fields, api


class ResUser(models.Model):
	_inherit = 'res.users'
	x_first_name = fields.Char(related='partner_id.x_first_name', inherited=True, readonly=False)
	x_name = fields.Char(related='partner_id.x_name', inherited=True, readonly=False)

	@api.onchange('x_name', 'x_first_name')
	def adjust_name(self):
		for user in self:
			name = ""
			if user.x_first_name:
				name = self.x_first_name
			if user.x_name:
				name = name + ' ' + self.x_name
			user.name = name

	@api.model_create_multi
	def create(self, vals_list):
		for vals in vals_list:
			if 'x_name' not in vals and 'name' in vals:
				vals['x_name'] = vals['name']
		return super().create(vals_list)
