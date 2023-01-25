from odoo import models, api, _
from odoo.exceptions import ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.constrains('acc_number')
    def _check_on_valid_iban(self):
        for record in self:
            if record.acc_number:
                acc_type = record.retrieve_acc_type(record.acc_number)
                if acc_type != 'iban':
                    raise ValidationError(_("Acc number %s is an invalid Iban ") % record.acc_number)
            self._check_on_bank_required()

    @api.constrains('bank_id')
    def _check_on_bank_required(self):
        for record in self:
            if not record.bank_id.id:
                raise ValidationError(_('There is no bank provided for bankaccount %s') % record.acc_number)

    @api.constrains('acc_number')
    def _validate_on_duplicate_iban(self):
        for record in self:
            other_iban = self.env['res.partner.bank'].with_context(active_test=False).sudo(). \
                search([('id', '!=', record.id)]).filtered(
                lambda l: l.sanitized_acc_number == record.sanitized_acc_number)
            if len(other_iban) > 0:
                raise ValidationError(_("Person or company %s has already Iban %s. You could assign a beneificiary ") %
                                      (other_iban[0].partner_id.display_name, record.acc_number))
