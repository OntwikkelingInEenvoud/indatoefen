from odoo import models, api


class AccountMove(models.Model):
	_inherit = 'account.move'

	#2023_0102 This method will be checked if running is still needed in v16
	def update_invoice_after_account_move_line_change(self):
		self._sync_dynamic_lines(True)