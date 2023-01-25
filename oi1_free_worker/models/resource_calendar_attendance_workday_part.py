from odoo import models, fields, api


class ResourceCalendarAttendanceWorkdayPart(models.Model):
	_name = "oi1_resource_calendar_attendance_workday_part"
	_description = "Workday Parts for the resource calendar"
	_order = 'sequence'

	sequence = fields.Integer(string='sequence', default=0, compute="_compute_sequence", store=True)
	code = fields.Char('code', required='true', compute="_compute_code", store=True, default='')
	name = fields.Char('name', compute='_compute_name')
	dayofweek = fields.Selection([
		('0', 'Monday'),
		('1', 'Tuesday'),
		('2', 'Wednesday'),
		('3', 'Thursday'),
		('4', 'Friday'),
		('5', 'Saturday'),
		('6', 'Sunday')
	], 'Day of Week', required=True, default='0')
	day_period = fields.Selection(
		[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('evening', 'Evening'), ('night', 'Night')], required=True,
		default='morning')

	@api.depends('dayofweek', 'day_period')
	def _compute_name(self):
		for day_part in self:
			selections = dict(self._fields['dayofweek'].selection)
			key_list = list(selections.keys())
			val_list = list(selections.values())
			name = val_list[key_list.index(day_part.dayofweek)] + "."
			selections = dict(self._fields['day_period'].selection)
			key_list = list(selections.keys())
			val_list = list(selections.values())
			name = name + val_list[key_list.index(day_part.day_period)]
			day_part.name = name

	@api.depends('dayofweek', 'day_period')
	def _compute_code(self):
		for day_part in self:
			selections = dict(self._fields['dayofweek'].selection)
			key_list = list(selections.keys())
			val_list = list(selections.values())
			day_part.code = val_list[key_list.index(day_part.dayofweek)] + "." + day_part.day_period

	@api.depends('dayofweek', 'day_period')
	def _compute_sequence(self):
		for day_part in self:
			sequence = 10 * int(day_part.dayofweek)
			if day_part.day_period == 'morning':
				sequence = sequence + 1
			if day_part.day_period == 'afternoon':
				sequence = sequence + 2
			if day_part.day_period == 'evening':
				sequence = sequence + 3
			if day_part.day_period == 'night':
				sequence = sequence + 4
			day_part.sequence = sequence
