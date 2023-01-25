from odoo import models, fields


class Transport(models.Model):
	_name = "oi1_transport"
	_description = "Transport"
	_order = 'sequence'

	sequence = fields.Integer(string='sequence', default=0)
	name = fields.Char('name', required='true')
