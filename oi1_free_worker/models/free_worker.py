from odoo import models, fields, api, exceptions, _
import datetime

def sanitize_account_number(acc_number):
    if acc_number:
        return re.sub(r'\W+', '', acc_number).upper()
    return False

class Freeworker(models.Model):
	_name = 'oi1_free_worker'
	_description = "Free worker"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_inherits = {'res.partner': 'partner_id'}
	_order = 'name, id'

	_sql_constraints = [
		('oi1_free_worker_partner_id_uniq',
		 'unique (partner_id)',
		 'A partner should be defined only once'),

		('oi1_free_worker_freeworker_code_uniq',
		 'unique (freeworker_code)',
		 'A free worker code should be unique'),
	]

	x_gender = fields.Selection([
		('m', 'Male'),
		('f', 'Female'),
		('fam', 'Family'),
	], string="Gender", default='', help="The gender of the free worker")
	poule_ids = fields.Many2many('oi1_freeworkerpoule', 'oi1_poule_free_worker_rel',
									   'free_worker_id', 'poule_id', string='Poules')
	partner_id = fields.Many2one('res.partner', string="Address", ondelete='restrict', auto_join=True, required=True)
	partner_residence_id = fields.Many2one('res.partner', string="Residence", tracking=True)
	residence_street_name = fields.Char(related="partner_residence_id.street_name", string="Residence street name",
										readonly=False)
	residence_street_number = fields.Char(related="partner_residence_id.street_number", string="Residence street number",
										  readonly=False, default='')
	residence_street_number2 = fields.Char(related="partner_residence_id.street_number2", string="Residence street number2",
										   readonly=False)
	residence_street = fields.Char(related="partner_residence_id.street", string="Residence street", readonly=False)
	residence_street2 = fields.Char(related="partner_residence_id.street2", string="Residence street2", readonly=False)
	residence_city = fields.Char(related="partner_residence_id.city", string="Residence city", readonly=False)
	residence_zip = fields.Char(related="partner_residence_id.zip", string="Residence zip", readonly=False)
	residence_country_id = fields.Many2one(related="partner_residence_id.country_id", string="Residence country",
										   readonly=False)
	freeworker_code = fields.Char(string="Freeworker code", help="The unique free worker code of the partner. "
									   "This number will be generated when the partner is a free worker ")
	education_ids = fields.Many2many('oi1_education', string='Educations')
	experience_level_ids = fields.Many2many('oi1_experience_level', string='Experience')
	birthdate = fields.Date(string="Birth date")
	general_experience_info = fields.Html(string="General experience info")
	agreement_with_principals = fields.Boolean("Agreement with principals")
	nationality_id = fields.Many2one('oi1_nationality', string="Nationality",
									 help="The nationality of the freeworker. "
										  "Only inhabitants of counties within the EU are allowed as a freeworker.",
									 tracking = True)
	resource_calendar_attendance_workday_part_ids = fields.Many2many('oi1_resource_calendar_attendance_workday_part',
																	 'free_worker_workday_rel', 'free_worker_id',
																	 'workday_id'
																	 , string="Workdays")
	travel_distance = fields.Selection(
		[('5 km', 'max.5 km'), ('10 km', 'max.10 km'), ('30 km', 'max.30 km'), ('50 km', 'max.50 km'),
		 ('>50 km', '>50 km')],
		required=True, default='>50 km', string="Max. Travel distance")
	transport_ids = fields.Many2many('oi1_transport', string="Transport")
	drivers_license = fields.Boolean(string="Drivers license")
	language_level_ids = fields.Many2many('oi1_language_level', string="Languages")
	is_from_commercial_partner_id = fields.Boolean(string="Is from commercial partner id",
												   compute="_compute_is_from_commercial_partner_id")
	education_text = fields.Html(string="Education")
	commercial_partner_id = fields.Many2one('res.partner', related="partner_id.commercial_partner_id", readonly=False,
											domain=[('x_is_freeworker', '=', True)],
											string="Beneficiary", tracking = True)
	active = fields.Boolean(string="Active", tracking = True, default=True)
	state = fields.Selection([
		('concept', 'Registered'),
		('checked', 'Checked'),
		('active', 'Active'),
		('old', 'History')
	], default='concept', tracking = True, string="Status")
	info = fields.Html(string="Info", help="General info of the freeworker which is visible for everyone")
	recruiter_partner_id = fields.Many2one('res.partner', string="Recruiter", domain=([('x_is_recruiter', '=', True)]),
										   help="Who has recruited the free worker"
										   )
	registration_date = fields.Date("Registration date", default=datetime.date.today())
	owner_company = fields.Many2one("res.company",  default=lambda self: self.env.company,
									help="Company who owns the freeworker data",
									string="Owner company", tracking=True)
	free_worker_label_ids = fields.Many2many('oi1_free_worker_label', 'oi1_free_worker_label_rel', 'free_worker_id', 'label_id')
	valid_registration_date = fields.Date(string="Valid registration", help="Has a valid identification code until this date")
	has_a_valid_legitimation = fields.Boolean(string="Has valid legitimation", compute="_compute_valid_legitimation")
	communication_partner_id = fields.Many2one('res.partner', string="Communication partner",
											   help="The person who is in charge of the communication of the free worker, "
													"this is mostly the practical assistant", tracking=True)
	communication_email = fields.Char(compute="_compute_communication_email", string="Mail voor Communication")
	has_a_communication_partner_id = fields.Boolean(compute="_compute_has_a_communication_partner_id")
	is_communication_email_different_from_email = fields.Boolean(compute="_compute_communication_email_different_from_email")
	bank_id = fields.Many2one(comodel_name='res.bank', related="bank_partner_bank_id.bank_id",
							  readonly=False, string="Related Bank")
	acc_number = fields.Char(string="Acc Number", related="bank_partner_bank_id.acc_number", readonly=False)
	bank_partner_bank_id = fields.Many2one(comodel_name="res.partner.bank", string="Free worker bank")


	@api.depends('email', 'commercial_partner_id')
	def _compute_communication_email_different_from_email(self):
		for free_worker in self:
			is_communication_email_different_from_email = True
			if len(free_worker.communication_email or '') == 0:
				is_communication_email_different_from_email = True
			else:
				if free_worker.email == free_worker.communication_email:
					is_communication_email_different_from_email = False
			free_worker.is_communication_email_different_from_email = is_communication_email_different_from_email

	def compute_state(self):
		for free_worker in self:
			if free_worker.valid_registration_date and free_worker.valid_registration_date < datetime.date.today():
				free_worker.state = 'concept'
			if free_worker.valid_registration_date and free_worker.valid_registration_date > datetime.date.today() \
					and free_worker.state == 'concept':
				free_worker.state = 'checked'
				continue

	@api.depends('communication_partner_id', 'email')
	def _compute_communication_email(self):
		for free_worker in self:
			if self.communication_partner_id.id:
				free_worker.communication_email = free_worker.communication_partner_id.email
			else:
				free_worker.communication_email = free_worker.email

	def copy(self, default=None):
		default = dict(default or {})
		partner = super().copy(default)
		partner.email = False
		partner.name = partner.name + _(" copy")
		partner.name = partner.x_name + _(" copy")
		return partner

	def unlink(self):
		for free_worker in self:
			free_worker.partner_id.active = False
			free_worker.active = False


	@api.depends('communication_partner_id')
	def _compute_has_a_communication_partner_id(self):
		for free_worker in self:
			if self.communication_partner_id.id:
				free_worker.has_a_communication_partner_id = True
			else:
				free_worker.has_a_communication_partner_id = False

	@api.depends('valid_registration_date')
	def _compute_valid_legitimation(self):
		for free_worker in self:
			has_a_valid_legitimation = False
			if free_worker.valid_registration_date and free_worker.valid_registration_date > fields.Date.today():
				has_a_valid_legitimation = True
			free_worker.has_a_valid_legitimation = has_a_valid_legitimation

	@api.model_create_multi
	def create(self, vals_list):
		for values in vals_list:
			if 'freeworker_code' not in values:
				values['freeworker_code'] = self._calc_x_freeworker_code()
			values['x_is_freeworker'] = True
		free_workers = super().create(vals_list)
		if len(vals_list) == 1:
			values = vals_list[0]
			bank_values = {}
			if 'bank_id' in values:
				bank_values['bank_id'] = values['bank_id']
			if 'acc_number' in values:
				bank_values['acc_number'] = values['acc_number']
			free_workers.save_bank_data(bank_values)
			free_workers.write(bank_values)
			free_workers.save_partner_bank_data(bank_values)
		return free_workers

	def save_bank_data(self, values):
		if 'acc_number' not in values and 'bank_id' not in values:
			return
		for free_worker in self:
			bank_values = {'partner_id':  free_worker.partner_id.id}
			if 'acc_number' in values:
				acc_number = values['acc_number'] or ''
				if acc_number == '':
					continue
				bank_values['acc_number'] = acc_number
				values.pop('acc_number')
			if 'bank_id' in values:
				bank_values['bank_id'] = values['bank_id'] or ''
				values.pop('bank_id')
			if free_worker.bank_partner_bank_id.id:
			   free_worker.bank_partner_bank_id.write(bank_values)
			   continue
			if not free_worker.bank_partner_bank_id.id:
				res_partner_bank_obj = self.env['res.partner.bank']
				res_partner_bank = res_partner_bank_obj.create(bank_values)
				values['bank_partner_bank_id'] = res_partner_bank.id

	def save_partner_bank_data(self, values):
		for free_worker in self:
			if 'bank_partner_bank_id' in values:
				free_worker.write({'bank_ids': [(6, 0, [values['bank_partner_bank_id']])]})

	def write(self, values):
		self.save_bank_data(values)
		if 'freeworker_code' in values:
			free_workers = self.filtered(lambda l: not len(l.freeworker_code or '') == 0)
			if len(free_workers) > 0:
				raise exceptions.UserError(_(
					"The freeworker code shouldn't be changed of a free worker"))
		if 'current_identification_document_id' in values:
			for freeworker in self:
				identification_document_id = values['current_identification_document_id']
				identification_document_ids = [identification_document_id]
				for identification_document_id in freeworker.identification_document_ids:
					identification_document_ids.append(identification_document_id.id)
				values['identification_document_ids'] = [(6, 0, identification_document_ids)]
				del values['current_identification_document_id']
		res = super().write(values)
		if 'active' in values:
			for freeworker in self:
				freeworker.partner_id.active = values['active']
		if 'commercial_partner_id' in values:
			self.mapped('partner_id').write({'commercial_partner_id': values['commercial_partner_id']})
			partner_id = self.env['res.partner'].browse([values['commercial_partner_id']])
			self.message_post(body=_("Beneficiary changed to %s") % partner_id.name)
		for freeworker in self.filtered(lambda l: len(l.freeworker_code or '') == 0):
			freeworker.freeworker_code = self._calc_x_freeworker_code()
		self.save_partner_bank_data(values)
		return res

	def _calc_x_freeworker_code(self):
		sequence = self.env['ir.sequence'].search([('name', '=', 'oi1_werkstandbij.res_partner_freeworker_seq')])
		return sequence[0].next_by_id()

	@api.depends('identification_document_ids')
	def _compute_current_identification_document_id(self):
		for partner in self:
			if len(partner.identification_document_ids) > 0:
				partner.current_identification_document_id = partner.identification_document_ids[0]
			else:
				partner.current_identification_document_id = False

	def _save_partner_bank_id(self, res_partner_bank_id_id):
		partner_bank_obj = self.env['res.partner.bank']
		for rp in self:
			if rp.id != rp.commercial_partner_id.id:
				raise exceptions.UserError(
					_(
						"Adjusting of the bank account is not allowed for the benificiary %s ") % rp.commercial_partner_id.name)
			partner_bank_ids = partner_bank_obj.search(
				[('partner_id', '=', rp.id), ('company_id', '=', self.env.user.company_id.id)])
			for partner_bank_id in partner_bank_ids:
				if partner_bank_id.id == res_partner_bank_id_id and partner_bank_id.sequence != 1:
					partner_bank_id.sequence = 1
					message = _("Bank account changed to %s" % partner_bank_id.acc_number)
					rp.message_post(body=message)
					continue
				partner_bank_id.sequence = 2
		return True

	@api.depends('commercial_partner_id')
	def _compute_is_from_commercial_partner_id(self):
		for freeworker in self:
			if not freeworker.commercial_partner_id.id:
				freeworker.commercial_partner_id = freeworker.partner_id
			if freeworker.commercial_partner_id.id != freeworker.partner_id.id:
				freeworker.is_from_commercial_partner_id = True
			else:
				freeworker.is_from_commercial_partner_id = False

	@api.depends('commercial_partner_id', 'partner_id.bank_ids')
	def _compute_partner_bank_id(self):
		bank_obj = self.env['res.partner.bank']
		for free_worker in self:
			x_partner_bank_id = False
			bank_ids = bank_obj.search(
				[('partner_id', '=', free_worker.commercial_partner_id.id),
				 ('company_id', '=', self.env.company.id)])
			if len(bank_ids) > 0:
				x_partner_bank_id = bank_ids[0]
			free_worker.partner_bank_id = x_partner_bank_id

	def do_action_check_private_data(self):
		return {
			'name': _('Register identification data'),
			'res_model': 'oi1_identification_data_wizard',
			'view_mode': 'form',
			'context': "{'default_free_worker_id':" + str(self.id) + "}",
			'target': 'new',
			'type': 'ir.actions.act_window',
			}




