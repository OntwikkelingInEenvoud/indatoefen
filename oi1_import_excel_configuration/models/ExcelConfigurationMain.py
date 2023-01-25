from odoo import models, fields, api
import base64


class MassMailingMailTemplateImport(models.Model):
    _name = 'oi1_import_excel_configuration.excel_main'
    _description = 'Excel configuration wizard'

    name = fields.Char(string='Description')
    template_id = fields.Many2one('oi1_import_excel_configuration.template_main', string="Template")
    fieldseparator = fields.Char(string="Field separator", required=True, default=",")
    startpos = fields.Integer(string="Reading from line", required=True, default=0)
    detail_ids = fields.One2many('oi1_import_excel_configuration.detail', 'main_id')
    module = fields.Char(related="template_id.module")

    @api.model_create_multi
    def create(self, vals_list):
        importTemplates = super().create(values)
        for importTemplate in importTemplates:
            if  importTemplate.template_id.id:
                self._set_templates_lines(importTemplate, importTemplate.template_id.id)
        return importTemplates

    def _set_templates_lines(self, excelconfmain, id_template):
        conf_detail_obj = self.env['oi1_import_excel_configuration.detail']
        conf_details = []
        template = self.env['oi1_import_excel_configuration.template_main'].browse(id_template_id)
        for detail_id in excelconfmain.detail_ids:
            detail_id.unlink()
        for temp_detail in template.detail_ids:
            conf_detail = conf_detail_obj.create({'main_id': excelconfmain.id,
                                                  'template_detail_id': temp_detail.id,
                                                  })
            conf_details.append(conf_detail.id)
        excelconfmain.write({'detail_ids': [(6, 0, conf_details)]})

    def write(self, values):
        if 'template_id' in values:
            for template in self:
                template._set_templates_lines(self, values['template_id'])
        return super().write(values)

    @api.model
    def get_excel_values(self, excel_configuration, data_file):
        base_import_obj = self.env['base_import.import']
        data_file = base64.b64decode(data_file)
        base_import = base_import_obj.create({'file': data_file})
        excel_values = base_import._read_file(None)
        records = []
        number = 1
        for ExcelValue in excel_values:
            if number > excel_configuration.startpos:
                print(number)
                excel_fields = {}
                for detail in excel_configuration.detail_ids:
                    if detail.pos and len(detail.pos) > 0:
                        try:
                            pos = detail.pos
                            value = ''
                            for p in pos.split(','):
                                if p.startswith('$') and value.strip() == '':
                                    value = p[1:].strip()
                                else:
                                    if not p.isdigit() and not p.startswith('$'):
                                        new_value = 0
                                        count = 0
                                        for char in p[::-1]:
                                            char = char.upper()
                                            if count == 0:
                                                new_value = new_value + ord(char) - 64
                                            if count > 0:
                                                new_value = new_value + ((ord(char) - 64) * (count * 26))
                                            count = count + 1
                                        p = str(new_value)
                                    if p.isdigit():
                                        value = value + ' ' + ExcelValue[int(p) - 1]
                                    if not p.isdigit() and p.startswith('$'):
                                        value = value + p[1:].strip()
                            excel_fields[detail.name] = value.strip()
                        except IndexError:
                            continue
                records.append(excel_fields)
            number += 1
        return records
