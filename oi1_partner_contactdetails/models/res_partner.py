from odoo import models, fields, api


class ResPartner(models.Model):
	_inherit = 'res.partner'

	x_first_name = fields.Char(string="first name", size=25, default='')
	x_initials = fields.Char(string="Initials", size=10, default='')
	x_name = fields.Char(string="Organisation name", size=150, default="", help="The name of company_name")
	x_last_name = fields.Char(string="Last name", help="The last name of the individual",
							  compute="_compute_x_last_name", inverse="_inverse_x_last_name")
	x_contact_name = fields.Char(string="Contact naam", size=100, compute="_compute_contact_name", store=False)
	x_nickname = fields.Char(string="Nickname")

	@api.depends('company_type')
	def _compute_x_last_name(self):
		for partner in self:
			partner.x_last_name= partner.x_name

	def _inverse_x_last_name(self):
		for partner in self:
			partner.x_name = partner.x_last_name

	@api.model_create_multi
	def create(self, vals_list):
		for vals in vals_list:
			if 'name' not in vals:
				initials = vals.get('x_initials', '')
				firstname = vals.get('x_first_name', '')
				x_name = vals.get('x_name', '')
				x_nickname = vals.get('x_nickname', '')
				vals['name'] = self._calculate_name(initials, firstname, x_name, '', x_nickname)
			if 'x_name' not in vals and 'name' in vals:
				name = vals['name']
			if 'name' in vals and 'x_name' not in vals:
				vals['x_name'] = name
			if 'x_name' not in vals and 'type' in values:
				partner_type = values['type']
				if partner_type not in ('contact'):
					values['x_name'] = ''
		return super().create(vals_list)

	def write(self, values):
		if ('x_name' in values or 'x_first_name' in values or 'x_initials' in values or 'x_nickname' in values) and 'name' not in values:
			for partner in self:
				if not partner.is_company:
					x_name = values.get('x_name', partner.x_name)
					x_first_name = values.get('x_first_name', partner.x_first_name)
					x_initials = values.get('x_initials', partner.x_initials)
					x_nickname = values.get('x_nickname', partner.x_nickname)
					x_last_name = values.get('x_last_name', partner.x_last_name)
					name = self._calculate_name(x_initials, x_first_name, x_name, x_last_name, x_nickname, partner.type)
					if name != partner.name:
						values['name'] = name
		return super().write(values)

	@api.onchange('company_id')
	def set_default_company_id(self):
		for rp in self:
			if not rp.country_id.id:
				rp.country_id = self.env.company.country_id

	def on_change_company_type(self, company_type):
		self.adjust_name()
		return super().on_change_company_type(company_type)

	@api.onchange('x_name', 'x_first_name', 'x_initials', 'x_last_name')
	def adjust_name(self):
		for rp in self:
			rp.name = self._calculate_name(rp.x_initials, rp.x_first_name, rp.x_name, rp.x_last_name, rp.x_nickname, rp.type)

	@api.depends('name', 'x_first_name', 'x_initials','is_company', 'parent_id.name', 'type', 'company_name', 'x_last_name')
	def _compute_contact_name(self):
		for contact in self:
			name = contact.name or ''
			if contact.x_name:
				name = contact.x_name
			contact_name = name
			if contact.x_initials and not contact.is_company:
				contact_name = contact.x_initials + ' ' + contact.x_last_name
			if contact.x_first_name and not contact.is_company:
				contact_name = contact.x_first_name + ' ' + contact.x_last_name
			contact.x_contact_name = contact_name.strip()

	@api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name', 'x_first_name')
	def _compute_display_name(self):
		diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=False)
		names = dict(self.with_context(**diff).name_get())
		for partner in self:
			partner.display_name = names.get(partner.id)

	@api.model
	def _calculate_name(self, initials, firstname, x_name, x_last_name, x_nickname, type=False):
		name = ''
		if x_name:
			name = x_name
		if firstname and type == 'contact':
			name = firstname + ' ' + x_last_name
		if initials and type == 'contact' and len(firstname or '') == 0:
			name = initials + ' ' + x_last_name
		if len(x_nickname or '') > 0:
			name = name + '(' + x_nickname + ')'
		return name.strip()

