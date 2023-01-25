from odoo import models, fields, api


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	x_del_date = fields.Date('Delivered_date')
	x_surcharge_amount = fields.Monetary("Surcharge amount", default=0.0)
	x_sales_analytic_account_line_ids = fields.One2many('account.analytic.line', 'x_sale_invoice_line_id',
														string="Sales analytic account ids")
	x_purchase_analytic_account_line_ids = fields.One2many('account.analytic.line', 'x_pur_invoice_line_id',
														   string="Purchase analytic account ids")
	x_sale_id = fields.Many2one('sale.order', compute="_compute_x_sale_id", store=True, string="sale order")
	x_payment_invoice_id = fields.Many2one('account.move', help="Serves for payment of invoice")

	@api.depends('x_sales_analytic_account_line_ids')
	def _compute_x_sale_id(self):
		for account_move_line in self:
			sale_id = False
			for account_analytic_line in account_move_line.x_sales_analytic_account_line_ids:
				if not sale_id:
					sale_id = account_analytic_line.x_sale_id
			account_move_line.x_sale_id = sale_id

	# 2021_0827 Replaces the function set_vat_pur_invoice_free_worker and is moved to the account.move.line as a property
	def set_vat_move_line_for_free_worker(self):
		for invoice_line in self:
			partner_id = invoice_line.move_id.partner_id
			print("set partner has vat on invoice")
			print(partner_id.x_has_vat_on_invoice)
			if not partner_id.x_has_vat_on_invoice:
				invoice_line.write({'tax_ids': False})
				return
			if invoice_line.move_id.partner_id.x_has_vat_on_invoice:
				tax_ids = invoice_line.get_taxes_purchase_product_id(invoice_line.product_id,
																	 invoice_line.move_id.partner_id)
				invoice_line.update_account_invoice_move_line({'tax_ids': tax_ids})

	def write(self, values):
		res = super().write(values)
		if 'quantity' in values and not self.env.context.get("surcharge_calc", False):
			# 2020_0406 Quantity should not be calculated of the surcharge lines self
			invoice_lines = self.filtered(
				lambda r: r.product_id.id != self.env.ref('oi1_werkstandbij.invoice_surcharge_product').id)
			invoice_lines.mapped('move_id').set_surcharge_invoiceLine()
		return res

	def _copy_data_extend_business_fields(self, values):
		super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
		values['x_sales_analytic_account_line_ids'] = [(6, None, self.x_sales_analytic_account_line_ids.ids)]
		values['x_purchase_analytic_account_line_ids'] = [(6, None, self.x_purchase_analytic_account_line_ids.ids)]
		values['x_sale_id'] = self.x_sale_id.id

	def unlink(self):
		aal = False
		invoices = self.mapped('move_id')
		aal_obj = self.env['account.analytic.line']
		for Invoice_Line in self:
			if not aal:
				aals = aal_obj.search([('x_sale_invoice_line_id', '=', Invoice_Line.id)])
				if len(aals) > 0:
					aal = aals[0]
		super().unlink()
		invoices.set_surcharge_invoiceLine()
		if aal:
			aal.check_invoiced()
