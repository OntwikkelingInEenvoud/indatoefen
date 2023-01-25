from odoo import models, fields, api, exceptions, _


class SaleCommissionPaymentLine(models.Model):
	_name = "oi1_sale_commission_payment_line"
	_description = "Sale commission payment line"

	date = fields.Date(string="Date", help="The date the commission line is generated")
	account_analytic_line_id = fields.Many2one('account.analytic.line', ondelete="restrict",
											   string="Hour Line", help="The hourline which genereted the commission line")
	oi1_sale_commission_id = fields.Many2one('oi1_sale_commission_payment', required=True, ondelete='restrict')
	qty = fields.Float(string="Qty", help=" The quantity of the commission payment")
	rate = fields.Monetary(string="Price Unit", help="The rate of the commission payment")
	amount = fields.Monetary(string="Amount", help="The total amount of the commission payment")
	currency_id = fields.Many2one('res.currency', string="Currency",
								  default=lambda self: self.env.company.currency_id, store=True)
	company_id = fields.Many2one('res.company', string='Company', required=True,
								 default=lambda self: self.env.company,
								 help="Company related to this commission")
	pur_invoice_line_id = fields.Many2one("account.move.line", string="Payment", help="The Invoice which is used to pay the commission")
	sale_id = fields.Many2one('sale.order', string="Sales order", ondelete="restrict", help="The sales order which created the commission payment")
	partner_worker_id = fields.Many2one('res.partner', string="Free worker",
										help="Free worker for which the commission is given")
	commission_payment_log_id = fields.Many2one('oi1_commission_payment_log', ondelete="restrict",
										 help="The related commission payment log which generated the commission line")
	commission_id = fields.Many2one('oi1_commission', ondelete="restrict", string="Commission", required=True,
									help="The name of the commission of the commission line")
	unit = fields.Selection([('hours', 'hours'), ('days', 'days'), ('weeks', 'weeks'), ('qty', 'qty')], string="Unit", default='hours')
	name = fields.Char(string="Description")
	reservation_commission_payment_line_id = fields.Many2one('oi1_sale_commission_payment_line', string="Reservation payment line", ondelete='restrict')
	code = fields.Char(string="Code", default='')
	type = fields.Selection([('commission', 'Commission'), ('reservation', 'Reservation'),('payment', 'payment')],
							default='commission', string='Type')
	has_a_reservation = fields.Boolean(compute="_compute_has_a_reservation", store=True, string="Has a reservation")

	@api.depends('reservation_commission_payment_line_id')
	def _compute_has_a_reservation(self):
		for sale_commission_payment_line in self:
			has_a_reservation = False
			if sale_commission_payment_line.reservation_commission_payment_line_id.id:
				has_a_reservation = True
			sale_commission_payment_line.has_a_reservation = has_a_reservation

	@api.constrains('sale_id', 'partner_worker_id')
	def _check_related_sale_id_partner_worker_id(self):
		for payment in self:
			if not payment.sale_id.id and not payment.partner_worker_id.id:
				raise exceptions.UserError(_('Please provide sale order of a partner related to the hour line'))

	@api.constrains('unit', 'account_analytic_line_id')
	def _check_account_analytic_line_id(self):
		for payment_line in self:
			if payment_line.unit == 'hours' and not payment_line.account_analytic_line_id.id:
				raise exceptions.UserError(_('Please provide a hour line when payment by hours'))
			if payment_line.unit != 'hours' and payment_line.account_analytic_line_id.id:
				raise exceptions.UserError(_('Please provide only an hour line when payment by hours'))

	def create(self, values):
		res = super(SaleCommissionPaymentLine, self).create(values)
		if res:
			SaleCommissionPaymentLine.calculate_payment_amounts(res)
		return res

	@staticmethod
	def calculate_payment_amounts(payment_lines):
		for payment_line in payment_lines:
			payments = []
			payment = payment_line.oi1_sale_commission_id
			if payment.id not in payments:
				payments.append(payment.id)
				payment.cmp_total_payment_amount()

	def write(self, values):
		res = super(SaleCommissionPaymentLine, self).write(values)
		SaleCommissionPaymentLine.calculate_payment_amounts(self)
		return res

	@api.model
	def search(self, args, offset=0, limit=None, order=None, count=False):
		uid = self.env.uid;
		args += ['|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)]
		return super(SaleCommissionPaymentLine, self).search(args, offset, limit, order, count);
