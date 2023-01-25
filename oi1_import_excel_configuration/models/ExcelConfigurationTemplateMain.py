from odoo import models, fields


class MassMailingMailTemplateImport(models.Model):
    _name = 'oi1_import_excel_configuration.template_main'
    _description = 'Excel configuration template'

    name = fields.Char(string='Description')
    module = fields.Char(string='Module')
    detail_ids = fields.One2many('oi1_import_excel_configuration.template_detail', 'main_id')
