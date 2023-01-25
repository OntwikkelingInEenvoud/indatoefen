from odoo import models, fields, api

import base64
import logging

_logger = logging.getLogger(__name__)


class ExcelImportWizard(models.TransientModel):
	_name = 'oi1_excelimportwizard'
	_description = 'Import Excel into Odoo'

	data_file = fields.Binary(string='Excel bestand', required=True)
	odoo_object = fields.Selection(([('', ''),
									 ('account.account', 'Grootboekschema'),
									 ('res.partner', 'Relaties'),
									 ('res.partner.category','Relatiegroepen'),
									 ('mail.message','Berichten / Notificaties'),
									 ('mail.activity', 'Activiteiten'),
									 ('ir.attachment', 'Bijlagen/Documenten'),
									 ]), default='')

	excel_configuration_id = fields.Many2one('oi1_import_excel_configuration.excel_main', required=True)


	def do_import_file(self):
		self.ensure_one();
		records = self._get_excelvalues
		print(records)
		if self.odoo_object == 'account.account':
			OdooImport_obj = self.env['oi1_odooimport']
			OdooImport = OdooImport_obj.create({});
			OdooImport.do_import_account_records(records)
			exit
		if self.odoo_object == 'res.partner':
			OdooImport_obj = self.env['oi1_odooimport']
			OdooImport = OdooImport_obj.create({});
			OdooImport.do_import_res_partner_records(records);
			exit
		if self.odoo_object == 'res.partner.category':
			OdooImport_obj = self.env['oi1_odooimport']
			OdooImport = OdooImport_obj.create({});
			OdooImport.do_import_product_category(records);
			exit
		if self.odoo_object == 'mail.message':
			OdooImport_obj = self.env['oi1_odooimport']
			OdooImport = OdooImport_obj.create({});
			OdooImport.do_import_mail_message(records);
			exit
		if self.odoo_object == 'mail.activity':
			OdooImport_obj = self.env['oi1_odooimport']
			OdooImport = OdooImport_obj.create({});
			OdooImport.do_import_mail_activity(records);
			exit
		if self.odoo_object == 'ir.attachment':
			OdooImport_obj = self.env['oi1_odooimport']
			OdooImport = OdooImport_obj.create({});
			OdooImport.do_import_attachments(records);
			exit
		return records

	@property
	def _get_excelvalues(self):
		Base_Import_Obj = self.env['base_import.import'];
		contact_file = base64.b64decode(self.data_file);
		Base_Import = Base_Import_Obj.create({'file': contact_file})
		ExcelValues = Base_Import._read_xlsx(None);

		Excelconfiguration = self.excel_configuration_id;
		records = [];
		number = 1;

		for ExcelValue in ExcelValues:
			if (number > Excelconfiguration.startpos):
				print(number);
				fields = {}
				for detail in Excelconfiguration.detail_ids:
					if detail.pos != False and detail.pos != '':
						try:
							pos = detail.pos
							value = ''
							for p in pos.split(','):
								if p.startswith('$') and value.strip() == '':
									value = p[1:].strip()
								else:
									if not p.isdigit() and not p.startswith('$'):
										newvalue =0
										count = 0
										for char in p[::-1]:
											char = char.upper()
											if count == 0:
												newvalue = newvalue + ord(char) - 64
											if count > 0:
												newvalue = newvalue + ((ord(char) - 64) * (count * 26))
											count = count + 1;
										p = str(newvalue)
									if p.isdigit():
										value = value + ' ' + ExcelValue[int(p) - 1];
									if not p.isdigit() and p.startswith('$'):
										value = value + p[1:].strip()
							fields[detail.name] = value.strip();
						except IndexError:
							continue;
				records.append(fields);
			number += 1;
		return records;
