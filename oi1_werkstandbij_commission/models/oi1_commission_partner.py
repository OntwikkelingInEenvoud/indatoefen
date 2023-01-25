from odoo import models, fields, api, exceptions
from datetime import date


class Commission(models.Model):
    _name = "oi1_commission_partner"
    _description = "Commission Partner"
    _inherits = {'oi1_commission_main': 'main_id'}

    main_id = fields.Many2one('oi1_commission_main', required=True, ondelete='restrict', auto_join=True)
    commission_role_id = fields.Many2one(related="commission_id.commission_role_id")

    @api.constrains('commission_id')
    def _check_if_commission_has_role(self):
        for commission in self:
            if not commission.commission_role_id.id:
                raise exceptions.UserError("Commission %s has no related role" % commission.commission_id.name)

    @api.constrains('commission_id')
    def _check_one_role_for_each_partner(self):
        for commission in self:
            commissions = commission.partner_id.x_oi1_commission_partner_ids.filtered(
                lambda l: l.commission_role_id.id == commission.commission_role_id.id
                )
            if len(commissions) > 1:
                warning_commission = commissions[0]
                raise exceptions.UserError("Commission %s has already the role %s defined for partner %s" % \
                              (warning_commission, warning_commission.commission_role_id.name,
                               warning_commission.partner_id.name))

    @api.model
    def get_commission_main(self, partner_id, commission_role_id, company_id=False, book_date= date.today()):
        commission_main_obj = self.env['oi1_commission_main']
        if not company_id:
            company_id = self.env.company
        if partner_id.id:
            commission_main_partners = self.search([('partner_id', '=', partner_id.id),
                                               ('commission_role_id', '=', commission_role_id.id),
                                               ('company_id', '=', company_id.id),
                                               ])
            if len(commission_main_partners) > 0:
                return commission_main_partners[0].mapped('main_id')
        return commission_main_obj.search([('id', '=', -1)])


