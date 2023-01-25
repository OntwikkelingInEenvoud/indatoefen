from odoo import models, fields, api
from odoo.exceptions import except_orm, ValidationError




class invoice_refund(models.TransientModel):
	_inherit = 'account.move.reversal'



	def invoice_refund(self):
		context = dict(self._context or {})
		Account_Invoice_obj = self.env['account.move'];
		Invoice_id = context.get('active_id', False)
		result = super().invoice_refund();
		if result:
			Invoice_old = Account_Invoice_obj.browse([Invoice_id]);
			Invoice_news = Account_Invoice_obj.search([('invoice_origin', '=', Invoice_old.number)])
			if len(Invoice_news) > 1:
				Invoice_new = Invoice_news[0];
			Old_Lines = Invoice_old.invoice_line_ids
			for Old_Line in Old_Lines:
				print(Old_Line);
		return result;
