from odoo import exceptions, models, fields, api, _
import json


class FreeWorkerDataCheckWizard(models.TransientModel):
    _name = 'oi1_free_worker_data_wizard'
    _description = 'freeworker check data wizard'

    free_worker_id = fields.Many2one('oi1_free_worker', required=True, string="Free worker")
    agreement_with_principals = fields.Boolean(string='Agreement_with_principals')
    naw_data_correct = fields.Boolean(string="NAW data ok")
    has_iban = fields.Boolean(string="Has iban")

    def _compute_naw_data_correct(self):
        if not self.free_worker_id.id:
             return False
        free_worker = self.free_worker_id
        naw_data_correct = True
        if not free_worker.city or free_worker.city == "":
            naw_data_correct = False
        if not free_worker.street_name  or free_worker.street_name == "":
            naw_data_correct = False
        if not free_worker.street_number or free_worker.street_number == "":
            naw_data_correct = False
        if not free_worker.zip or free_worker.zip == "":
            naw_data_correct = False
        return naw_data_correct

    @api.onchange('free_worker_id')
    def get_free_worker_values(self):
        for wizard in self:
            if wizard.free_worker_id.id:
               wizard.agreement_with_principals = wizard.free_worker_id.agreement_with_principals
               wizard.naw_data_correct = wizard._compute_naw_data_correct()
               has_iban = False
               iban =  wizard.free_worker_id.x_partner_bank_id
               if iban and iban != "":
                   has_iban = True
               wizard.has_iban = has_iban

            else:
               wizard.agreement_with_principals = False
               wizard.naw_data_correct = False
               wizard.has_iban = False

    def do_send_fill_naw_data(self):
        self.ensure_one()
        self.do_save_data()
        if not self.free_worker_id.id:
            raise exceptions.UserError(_('The is no free worker related to the wizard'))
        if self.naw_data_correct:
            raise exceptions.UserError(_('The free worker has completely filled in the NAW-data'))
        template = self.env.ref('oi1_free_worker_data_check.mail_complete_nav')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = dict(
            default_model='oi1_free_worker',
            default_res_id=self.free_worker_id.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def do_send_mail_iban(self):
        self.ensure_one()
        self.do_save_data()
        if not self.free_worker_id.id:
            raise exceptions.UserError(_('The is no free worker related to the wizard'))
        if self.has_iban:
            raise exceptions.UserError(_('The free worker has completely filled in the iban data'))
        template = self.env.ref('oi1_free_worker_data_check.mail_send_iban')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = dict(
            default_model='oi1_free_worker',
            default_res_id=self.free_worker_id.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def do_send_sign_agreement_with_principals(self):
        self.ensure_one()
        self.do_save_data()
        if not self.free_worker_id.id:
            raise exceptions.UserError(_('The is no free worker related to the wizard'))
        if self.agreement_with_principals:
            raise exceptions.UserError(_('The free worker has agreeed with the principals'))
        template = self.env.ref('oi1_free_worker_data_check.sign_agreement_template_email')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = dict(
                default_model='oi1_free_worker',
                default_res_id=self.free_worker_id.id,
                default_use_template=bool(template),
                default_template_id=template.id,
                default_composition_mode='comment',
                )
        return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': ctx,
        }

    def do_save_data(self):
        for wizard in self:
            if not wizard.free_worker_id.id:
                raise exceptions.UserError(_('The is no free worker related to the wizard'))
            free_worker = wizard.free_worker_id
            free_worker.agreement_with_principals = wizard.agreement_with_principals



