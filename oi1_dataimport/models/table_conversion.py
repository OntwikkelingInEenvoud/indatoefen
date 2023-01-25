from odoo import models, fields


class TableConversion(models.Model):
    _name = 'oi1_dataimport.table_conversion'
    _description = 'table conversion values'

    prev_code = fields.Char(string="Former Unique code")
    prev_table_name = fields.Char(string="TableName")
    prev_table_info = fields.Char(string="TableInfo")
    res_model_name = fields.Char(string="model_name")
    res_id = fields.Integer(string="id")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self._compute_default_company(),
                                 required=True)

    def _compute_default_company(self):
        return self.env['res.company'].browse([1])
