from odoo import models, fields, api, exceptions
from odoo import _


class poulerate(models.Model):
	_name = "oi1_poule_rate"
	_description = "Poule rate"


	def _get_currency_id(self):
		for poule_rate in self:
			poule_rate.currency_id = self.env.user.company_id.currency_id;

	name = fields.Char('Name');
	description = fields.Char('Description')
	prio = fields.Integer('Rule Priority', default=0)
	poule_id = fields.Many2one('oi1_freeworkerpoule', string="Worker poule")
	partner_id = fields.Many2one('res.partner', string='Freeworker')
	type = fields.Selection([
		('time', 'Tijdstip'),
		('duration', 'Tijdsduur'),
	], default='duration')
	from_time = fields.Char(string='Start', size=5)
	to_time = fields.Char(string='End', size=5)
	daytype = fields.Selection([
		('all', 'All dagen'),
		('mon', 'Maandag'),
		('tue', 'Dinsdag'),
		('wed', 'Woensdag'),
		('thur', 'Donderdag'),
		('fri', 'Vrijdag'),
		('sat', 'Zaterdag'),
	], default='all')

	hourrate = fields.Monetary('hour rate')
	currency_id = fields.Many2one('res.currency', compute='_get_currency_id', string="Currency")
	company_id = fields.Many2one('res.company', string='Company', required=True,
								 default=lambda self: self.env.user.company_id,
								 help="Company related to this poule")

	@api.onchange('from_time')
	def checkStartTime(self):
		self.from_time = self._checkTime(self.from_time);

	@api.onchange('to_time')
	def checkEndTime(self):
		self.to_time = self._checkTime(self.to_time);

	def _checkTime(self, time):
		if time == False:
			return False;
		time = time.replace('.', ':');
		time = time.replace(',', ':');
		if len(time) == 4:
			time = '0' + time;
		if time[2:3] != ':':
			raise exceptions.UserError(_("The time should contain a :"));
		return time;
