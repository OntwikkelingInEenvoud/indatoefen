from odoo import models, api


class IdentificationDataWizard(models.TransientModel):
    _name = 'convert_free_worker_identification_data'
    _description = 'convert_free_worker_identification_data'

    @api.model
    def convert_identification_data(self):
        wizard_obj = self.env['oi1_identification_data_wizard']
        free_worker_obj = self.env['oi1_free_worker']
        free_workers = free_worker_obj.search([])
        for free_worker in free_workers:
            values = {'free_worker_id': free_worker.id}
            field_count = 0
            if len(free_worker.ssn or '') > 0:
                values['ssn'] = free_worker.ssn
                field_count += 1
            if free_worker.current_identification_document_id.id:
                if free_worker.current_identification_document_id.document_type_id.id:
                    values['document_type_id'] = free_worker.current_identification_document_id.document_type_id.id
                    field_count +=1
                if free_worker.current_identification_document_id.code:
                    values['code'] = free_worker.current_identification_document_id.code
                    field_count +=1
                if free_worker.current_identification_document_id.expiration_date:
                    values['expiration_date'] = free_worker.current_identification_document_id.expiration_date
                    field_count +=1
            wizard = wizard_obj.create(values)
            if field_count > 0:
                if free_worker.current_identification_document_id.id:
                    if free_worker.current_identification_document_id.expiration_date:
                        wizard.do_agree_save_data()
                        continue
                wizard.do_save_data()


