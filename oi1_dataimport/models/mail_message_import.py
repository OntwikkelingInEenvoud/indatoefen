from odoo import models
from datetime import datetime

class MailMessageImport(models.TransientModel):

	_inherit = 'oi1_odooimport'

	def do_import_mail_message(self, records):
		mail_message_obj =  self.env['mail.message']
		table_conversion_obj = self.env['oi1_dataimport.table_conversion']

		for record in records:
			mm = False
			model = False
			res_id = False
			body = ''
			print(record)

			if 'body' in record:
				body = record['body'].strip()

			if 'crm_lead_x_prev_code' in record:
				x_prev_code = record['crm_lead_x_prev_code'].strip()
				if x_prev_code != '':
					tables = table_conversion_obj.search([('prev_code', '=', x_prev_code),
														  ('res_model_name', '=', 'crm.lead')
														  ])
					if len(tables) > 0:
						res_id = tables[0].res_id
						model = 'crm.lead'
			if not model and 'partner_id_x_prev_code' in record:
				x_prev_code = record['partner_id_x_prev_code'].strip()
				if x_prev_code != '':
					tables = table_conversion_obj.search([('prev_code', '=', x_prev_code),
														  ('res_model_name', '=', 'res.partner')
														  ])
					if len(tables) > 0:
						res_id = tables[0].res_id
						model = 'res.partner'
			if 'x_prev_code' in record:
				prev_code = record['x_prev_code']
				tables = table_conversion_obj.search([('prev_code', '=', prev_code),
													  ('res_model_name', '=', 'mail.message')
													  ])
				if len(tables) > 0:
					mm = mail_message_obj.browse([tables[0].res_id])[0]
				if not mm and body != '':
					if res_id:
						mm = mail_message_obj.sudo().create({'model': model, 'res_id' : res_id, 'body' : body})
			if not mm:
				continue
			if model:
				mm.model = model
			if res_id:
				mm.res_id = res_id
			if 'subject' in record:
				mm.subject = record['subject']
			if 'message_type' in record:
				mm.message_type = record['message_type']
			if 'date' in record:
				str_date_deadline = record['date']
				str_date_deadline = str_date_deadline.replace('00:00:00', '');
				str_date_deadline = str_date_deadline.strip()
				dateparts = str_date_deadline.split(' ');
				if len(dateparts) > 1:
					str_date_deadline = dateparts[0]
				yearpos = str_date_deadline.find('-')
				date = False
				if yearpos < 3:
					date = datetime.strptime(str_date_deadline, '%d-%m-%Y')
				if yearpos == 4:
					date = datetime.strptime(str_date_deadline, '%Y-%m-%d')
				if date:
					mm.date = date.strftime('%Y-%m-%d')
			if 'body' in record:
				mm.body = record['body']
			if 'subtype_id' in record:
				mm.subtype_id = record['subtype_id']

			if not mm.subtype_id.id:
				subtypes = self.env['mail.message.subtype'].with_context(lang='en_US').search([('name','=','Note')])
				if len(subtypes) > 0:
					mm.subtype_id = subtypes[0].id
			self.env.cr.commit();
			print(mm.id)
			self.set_table_conversion(prev_code, 'mail.message', '', mm.id)