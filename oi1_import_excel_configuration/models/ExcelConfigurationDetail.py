from odoo import models, fields


class MassMailingMailTemplateImport(models.Model):
    _name = 'oi1_import_excel_configuration.detail'
    _description = 'Excel configuration wizard'
    _order = "pos, id"

    name = fields.Char(related='template_detail_id.name', readonly=True)
    pos = fields.Char(string='Positions', default='')
    main_id = fields.Many2one('oi1_import_excel_configuration.excel_main')
    template_detail_id = fields.Many2one('oi1_import_excel_configuration.template_detail')
