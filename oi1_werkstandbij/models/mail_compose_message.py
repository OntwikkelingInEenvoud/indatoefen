from odoo import models


class MailComposer(models.TransientModel):
	_inherit = 'mail.compose.message'

	def send_mail(self, auto_commit=False):
		mail_message_obj = self.env['mail.message']
		for wizard in self:
			result = super().send_mail(auto_commit)
			active_model = self.env[wizard.model]
			if str(active_model) == 'account.move()':
				account_invoice = self.env['account.move'].browse([wizard.res_id])
				wsb_account_invoice = account_invoice.x_wsb_account_invoice
				# An mail send for the invoice should also logged in the WSB if there is an WSB-invoice
				if wsb_account_invoice.id and wizard.res_id:
					mail_message = mail_message_obj.search([('res_id', '=', wizard.res_id)], limit=1, order="id desc")
					if mail_message.message_type == 'comment':
						values = {'message_type': mail_message.message_type,
								  'res_id': wsb_account_invoice.id,
								  'model': mail_message.model,
								  'subject' : mail_message.subject,
								  'date': mail_message.date,
								  'body': mail_message.body,
								  'attachment_ids': [(6,0, mail_message.attachment_ids.ids)],
								  }
						mail_message_obj.sudo().create(values)
						for attachment_id in mail_message.attachment_ids:
							attachment_wsb_id = attachment_id.copy()
							attachment_wsb_id.sudo().write({'res_id': wsb_account_invoice.id,})
		return result
