from odoo import models


class CancelAgreeHourLine_Wizard(models.TransientModel):
	_name = "oi1_werkstandbij.cancel_agreehourline_wizard"
	_description = "Cancel agreed hour lines"

	def do_cancel_agreements(self):
		hourlines = self.env['account.analytic.line'].browse(self._context.get('active_ids', []))
		for hourline in hourlines:
			if not hourline.x_partner_id.id:
				continue
			if hourline.x_state != 'approved':
				continue
			hourline.write({'x_state': 'concept', 'system': True})
