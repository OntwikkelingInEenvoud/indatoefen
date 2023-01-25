from odoo import models, fields


class MassMailingMailTemplateImport(models.Model):
    _name = 'oi1_import_excel_configuration.template_detail'
    _description = 'Excel configuration template detail'
    _order = "name"

    name = fields.Char(string='Description')
    main_id = fields.Many2one('oi1_import_excel_configuration.template_main')
