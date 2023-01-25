from odoo import exceptions, models, fields, api, _
import json


class IdentificationDataWizard(models.TransientModel):
    _name = 'oi1_identification_data_wizard'
    _description = 'identification data wizard'

    free_worker_id = fields.Many2one('oi1_free_worker', required=True, string="Free worker")
    ssn = fields.Char(string="SSN")
    document_type_id = fields.Many2one('oi1_identification_document_type', string="Document type",
                                       help="The identification document type")
    nationality_id = fields.Many2one('oi1_nationality', string="Nationality", required=True)
    code = fields.Char(string="Code")
    expiration_date = fields.Date(string="Expiration date")

    c_type = "private"

    @api.onchange('free_worker_id')
    def _get_free_worker_data(self):
        document_type_obj = self.env['oi1_identification_document_type']
        for wizard in self:
            ssn = ""
            document_type_id = False
            code = ""
            expiration_date = False
            document_information = self._get_document_information(wizard.free_worker_id)
            print(document_information)
            if len(document_information) > 0:
                body = _("Identiteitsgegevens zijn ingezien door %s" % self.env.user.name)
                wizard.free_worker_id.message_post(body=body)
                data_dict = json.loads(document_information.document_info)
                print(data_dict)
                if 'ssn' in data_dict:
                    ssn = data_dict['ssn']
                if 'document_type_id' in data_dict:
                    document_type_id = document_type_obj.browse([data_dict['document_type_id']])
                if 'code' in data_dict:
                    code = data_dict['code']
                if 'expiration_date' in data_dict:
                    expiration_date = data_dict['expiration_date']
            wizard.ssn = ssn
            wizard.document_type_id = document_type_id
            wizard.code = code
            wizard.expiration_date = expiration_date
            wizard.nationality_id = wizard.free_worker_id.nationality_id


    def do_agree_save_data(self):
        for wizard in self:
            expiration_date = wizard.expiration_date
            nationality_id = wizard.nationality_id
            code = wizard.code
            document_type_id = wizard. document_type_id
            if not expiration_date:
                raise exceptions.UserError(
                    _("Please provide an expiration data for validating the identity of the free worker"))
            if not code:
                raise exceptions.UserError(
                    _("Please provide a document code for validating the identify of the free worker"))
            if not document_type_id:
                raise exceptions.UserError(
                    _("Please provide a document type for validating the identify of the free worker"))
            self.do_save_data()
            wizard.free_worker_id.valid_registration_date = expiration_date
            body = _("Identiteit is gevalideerd door %s" % self.env.user.name)
            free_worker_id = wizard.free_worker_id
            free_worker_id.message_post(body=body)
            if free_worker_id.state == 'concept':
                free_worker_id.state = 'checked'

    def do_save_data(self):
        document_information_obj = self.env['oi1_document_information']
        for wizard in self:
            dict_values = {'ssn': wizard.ssn or ''}
            if wizard.document_type_id.id:
                dict_values['document_type_id'] = wizard.document_type_id.id
            dict_values['code'] = wizard.code
            if wizard.expiration_date:
                dict_values['expiration_date'] = wizard.expiration_date.strftime('%Y-%m-%d')
            document_information = self._get_document_information(wizard.free_worker_id)
            if len(document_information) == 0:
                document_information = document_information_obj.create({'model_name': 'oi1_free_worker',
                                                                        'res_id': wizard.free_worker_id.id,
                                                                        'type': IdentificationDataWizard.c_type
                                                                        })
            json_string = json.dumps(dict_values)
            document_information.document_info = str(json_string)
            self._clean_wizard_data(wizard)
            wizard.free_worker_id.nationality_id = nationality_id

    def _clean_wizard_data(self, wizard):
        wizard.ssn = False
        wizard.document_type_id = False
        wizard.code = False
        wizard.expiration_date = False

    def _get_document_information(self, free_worker_id):
        document_information_obj = self.env['oi1_document_information']
        return document_information_obj.search([('model_name', '=', 'oi1_free_worker'),
                                                ('res_id', '=', free_worker_id.id),
                                                ('type', '=', IdentificationDataWizard.c_type),
                                                ])
