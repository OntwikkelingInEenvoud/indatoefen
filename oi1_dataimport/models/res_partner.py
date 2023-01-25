# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

_sql_constraints = [
    ('res.partner_x_prev_code',
     'unique (x_prev_code)',
     'The partner code should be unique')
]


class ResPartner(models.Model):
    _inherit = 'res.partner'
    x_prev_code = fields.Char(string="Debtor code", copy=False,
                         help="The unique code of this relation (for example the debtor of creditor code",
                        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'x_prev_code' not in vals or not vals['x_prev_code']:
                vals['x_prev_code'] = self._calc_x_code()
        partners = super(ResPartner, self).create(vals_list)
        return partners

    def write(self, values):
        if 'x_prev_code' not in values:
            for partner in self.filtered(lambda r: not r.x_prev_code):
                partner.write({'x_prev_code': self._calc_x_code()})
        return super(ResPartner, self).write(values)

    @api.model
    def _calc_x_code(self):
        sequence_name = 'oi1_dataimport.res_partner_debcode'
        sequences = self.env['ir.sequence'].search([('name', '=', sequence_name)])
        if len(sequences) == 0:
            raise exceptions.UserError(_('The sequence with the name %s is not found') % sequence_name)
        return sequences[0].next_by_id()
