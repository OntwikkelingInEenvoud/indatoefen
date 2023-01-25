from odoo import models, fields, api, exceptions, _
from datetime import datetime

class MailActivitityImport(models.TransientModel):

	_inherit = 'oi1_odooimport'

	def do_import_mail_activity(self, records):
		mail_message_obj =  self.env['mail.activity']
		table_conversion_obj = self.env['oi1_dataimport.table_conversion']

		for record in records:
			print(record)
			mc = False
			model = False
			res_id = False
			body = ''
			prev_code = False
			if 'crm_lead_id_x_prev_code' in record:
				x_prev_code = record['crm_lead_id_x_prev_code'].strip()
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
			activity_type = False;
			if 'type_name' in record:
				type_name = record['type_name']
				activity_types = self.env['mail.activity.type'].with_context(lang='en_US').search([('name','=', type_name)])
				if len(activity_types) > 0:
					activity_type = activity_types[0]
				if not activity_type:
					activity_type = self.env['mail.activity.type'].sudo().create({'name': type_name,
																				  'model': model,
																				  'res_id': res_id})

			if 'x_prev_code' in record:
				prev_code = record['x_prev_code']
				tables = table_conversion_obj.search([('prev_code', '=', prev_code),
													  ('res_model_name', '=', 'mail.activity')
													  ])
				if len(tables) > 0:
					mc = mail_message_obj.browse([tables[0].res_id])[0]
					print("Activitiy found als done, so no update %s" % mc.id)
					continue
				if not mc:
					res_model_ids = self.env['ir.model'].search([('model','=', model)])
					if len(res_model_ids)  > 0:
						res_model_id = res_model_ids[0]
					if res_id:
						mc = mail_message_obj.create({'res_id' : res_id, 'res_model_id' : res_model_id.id, 'activity_type_id':activity_type.id})
			if not mc:
				continue
			if activity_type:
				mc.activity_type_id = activity_type.id;
			if model:
				res_model_id = False;
				res_model_ids = self.env['ir.model'].search([('model', '=', model)])
				if len(res_model_ids) > 0:
					res_model_id = res_model_ids[0]
				if res_model_id:
					mc.model = model
					mc.res_model_id = res_model_id
			if res_id:
				mc.res_id = res_id
			if 'summary' in record:
				mc.summary = record['summary']
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
					mc.date = date.strftime('%Y-%m-%d')
					mc.date_deadline = date.strftime('%Y-%m-%d')
			if 'note' in record:
				mc.note = record['note']
			if 'make_old_ready' in record:
				if record['make_old_ready']:
					if mc.date_deadline <  datetime.now().date():
					   date_deadline = mc.date_deadline
					   id = mc.action_feedback();
					   if id:
						   message = self.env['mail.message'].browse([id])
						   if record['x_prev_code']:
							   message.x_prev_code = record['x_prev_code']
						   if date_deadline:
							   message.date = date_deadline.strftime('%Y-%m-%d')
			print(mc.id)
			self.set_table_conversion(prev_code, 'mail.activity', '', mc.id)
			self.env.cr.commit()