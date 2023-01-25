from odoo import models, fields, api, exceptions, _
import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def write(self, values):
        if 'x_current_identification_document_id' in values:
            for partner in self:
                identification_document_id = values['x_current_identification_document_id']
                identification_document_ids = [identification_document_id]
                for identification_document_id in partner.x_identification_document_ids:
                    identification_document_ids.append(identification_document_id.id)
                values['x_identification_document_ids'] = [(6, 0, identification_document_ids)]
                del values['x_current_identification_document_id']
        if 'commercial_partner_id' in values and not values['commercial_partner_id']:
            for partner in self:
                values['commercial_partner_id'] = partner.id
        result = super().write(values)
        return result

    x_min_commission_amount = fields.Float(string="Min.Commission amount",
                                           help="Minimum amount for automatic payment of commissions. "
                                                "Zero is no automatic payment",
                                           default=0.0)
    x_has_vat_on_invoice = fields.Boolean(string="Vat included", compute="_compute_x_has_vat_on_invoice")
    x_coc = fields.Char(string="COC", help="The COC number of the partner")

    x_is_recruiter = fields.Boolean(string="Is a Recruiter", help="The person recruits free workers", default=False)
    x_coc = fields.Char(string="COC", help="The COC number of the partner")
    x_is_a_sales_partner = fields.Boolean(string="Is a sales partner",
                                          help="The relation can act as a salespartner within orders", default=False)
    x_has_vat_on_invoice = fields.Boolean(string="Has Vat on invoice", default=True, tracking=True,
                                          help="Determines if BTW should be added on the invoices. " +
                                               "Normally a company should have vat on the invoice but under certain circumstances this could be different. Take care with this setting")

    @api.model
    def get_commission_period(self, partner, date):
        period = partner.x_commission_period
        if period == 'wk':
            return _("Week ") + str(date.year) + ("0" + str(date.strftime('%V')))[-2:]
        if period == 'mm':
            return _("Month ") + str(date.year) + ("0" + str(date.month))[-2:]
        if period == 'yy':
            return _("Year ") + str(date.year)
        return _("Manual")

    @api.depends("x_partner_bank_id")
    def _compute_x_bank_id(self):
        for partner in self:
            bank_id = False
            partner_bank_id = self._get_partner_bank_id(partner)
            if partner_bank_id:
               bank_id = partner_bank_id.bank_id
            partner.x_bank_id = bank_id

    @api.depends('x_identification_document_ids')
    def _compute_x_current_identification_document_id(self):
        for partner in self:
            if len(partner.x_identification_document_ids) > 0:
                partner.x_current_identification_document_id = partner.x_identification_document_ids[0]
            else:
                partner.x_current_identification_document_id = False

    @api.depends('is_company', 'parent_id.commercial_partner_id')
    def _compute_commercial_partner(self):
        self.env.cr.execute("""
         WITH RECURSIVE cpid(id, parent_id, commercial_partner_id, final) AS (
             SELECT
                 id, parent_id, 
                 CASE WHEN x_is_freeworker = True and commercial_partner_id is not null then commercial_partner_id else id end, 
                 (coalesce(is_company, false) OR parent_id IS NULL) as final
             FROM res_partner
             WHERE id = ANY(%s)
         UNION
             SELECT
                 cpid.id, p.parent_id, p.id,
                 (coalesce(is_company, false) OR p.parent_id IS NULL) as final
             FROM res_partner p
             JOIN cpid ON (cpid.parent_id = p.id)
             WHERE NOT cpid.final
         )
         SELECT cpid.id, cpid.commercial_partner_id
         FROM cpid
         WHERE final AND id = ANY(%s);
         """, [self.ids, self.ids])

        d = dict(self.env.cr.fetchall())
        for partner in self:
            fetched = d.get(partner.id)
            if fetched is not None:
                partner.commercial_partner_id = fetched
            elif partner.is_company or not partner.parent_id:
                partner.commercial_partner_id = partner
            else:
                partner.commercial_partner_id = partner.parent_id.commercial_partner_id

    @api.depends('commercial_partner_id')
    def _compute_x_is_from_commercial_partner_id(self):
        for rp in self:
            if not rp.commercial_partner_id.id:
                rp.commercial_partner_id = rp
            if rp.commercial_partner_id.id != rp.id:
                rp.x_is_from_commercial_partner_id = True
            else:
                rp.x_is_from_commercial_partner_id = False

    @staticmethod
    def _get_partner_bank_id(partner):
        bank_ids = partner.commercial_partner_id.bank_ids
        if len(bank_ids) > 0:
            return partner.bank_ids[0]
        return False

    @staticmethod
    def check_if_partner_has_a_beneficiary(partner):
        if partner.id == partner.commercial_partner_id.id:
            return False
        if partner.id != partner.commercial_partner_id.id:
            return True



