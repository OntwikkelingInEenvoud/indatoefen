from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Commission(models.Model):
    _name = "oi1_commission"
    _description = "Commission"

    name = fields.Char('name')
    description = fields.Char('description')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company,
                                 help="Company related to this commission")
    default_rate = fields.Monetary(string="Default rate", default=0.00)
    percentage = fields.Float(string="Percentage", default=0.00,
                              help="Percentage which sould be used when this amount is higher then the default rate."
                                   " Keep 0 voor no percenage")
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    commission_role_id = fields.Many2one('oi1_commission_role', string="Commission role")
    free_worker_commission = fields.Boolean(string="Free worker commission", compute="_compute_free_worker_commission",
                                            store=True)
    sub_commission_ids = fields.Many2many('oi1_commission', 'oi1_commission_sub_rel', 'commission_id',
                                          'sub_commission_id',
                                          string="The different commissions in which the commission is internal divided")
    commission_rate_list_id = fields.Many2one('oi1_commission_rate_list', string="Rates")
    payment_by = fields.Selection([('customer', 'Customer'), ('freeworker', 'Freeworker')], default='customer', required=True)
    commission_beneficiary_partner_id = fields.Many2one('res.partner', string="Beneficiary of the commission",
                                                        help="The benificary of the commission which overrules the normal partner within the commission")
    active = fields.Boolean(string="Active", help="If true then the commission is in use and can be selected. ", default=True)

    @api.constrains('commission_role_id', 'payment_by', 'commission_beneficiary_partner_id')
    def _check_payment_by_commission_role_id(self):
        free_worker_commission = self.env.ref('oi1_werkstandbij_commission.oi1_commission_role_free_worker_commission')
        for commission in self:
            if commission.commission_role_id.id == free_worker_commission.id and commission.payment_by != 'freeworker':
                raise ValidationError(_('For this commission the payment by should be by freeworker.'))
            if commission.commission_role_id.id == free_worker_commission.id and not commission.commission_beneficiary_partner_id.id:
                raise ValidationError(_('For this commission there should be a  payment by should be a commission_beneficiary_partner_id defined'))


    @api.constrains('commission_role_id')
    def _check_can_commission_role_id_be_changed(self):
        oi1_commission_log_obj = self.env['oi1_commission_log']
        for commission in self:
            count_commission_logs = oi1_commission_log_obj.search_count([('commission_id', '=', commission.id)])
            if count_commission_logs > 0:
                raise ValidationError(
                    _('This commission is already used with the role %s so this commission cannot be changed. Archive this commission instead and create a new one ') % commission.commission_role_id.name)


    def get_compute_calculation_rate(self, hour_rate, book_date):
        self.ensure_one()
        if self.commission_rate_list_id:
            return self.commission_rate_list_id.get_tariff_with_given_hour_rate(hour_rate, book_date)
        if self.percentage > 0 and hour_rate != 0.0:
            value = hour_rate * self.percentage
            if value > hour_rate:
                return value
        return self.default_rate



    @api.depends('commission_role_id')
    def _compute_free_worker_commission(self):
        free_worker_commission_id = self.env.ref(
            'oi1_werkstandbij_commission.oi1_commission_role_free_worker_commission')
        for commission in self:
            free_worker_commission = False
            if commission.commission_role_id.id and commission.commission_role_id.id == free_worker_commission_id.id:
                free_worker_commission = True
            commission.free_worker_commission = free_worker_commission

    def write(self, values):
        result = super().write(values)
        commission_main_obj = self.env['oi1_commission_main']
        if 'default_rate' in values:
            for commission in self:
                commission_mains = commission_main_obj.search([('commission_id', '=', commission.id),
                                                               ('use_default_rate', '=', True),
                                                               ])
                commission_mains.write({'default_rate': values['default_rate']})
        return result
