from uuid import uuid4
from odoo import models, fields, api
import base64, math
from Crypto.Cipher import AES

import logging

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _name = 'oi1_document_information'
    _description = 'Extra information over documents'

    document_info = fields.Char(string="document info", store=False, compute="_decrypt_document", inverse="_save_document",)
    document = fields.Char(string="document")
    model_name = fields.Char(string="model", required=True)
    res_id = fields.Integer(string="res_id", required=True)
    type = fields.Char(string="type", default='')

    COMMON_16_BYTE_IV_FOR_AES = b'IVIVIVIVIVIVIVIV'

    @api.model
    def get_common_cipher(self):
        cipher = AES.new(self._get_secret_key(), AES.MODE_CBC, self.COMMON_16_BYTE_IV_FOR_AES)
        return cipher

    @api.model
    def _get_secret_key(self):
        c_model = 'oi1_document_information'
        config_parameter_obj = self.env['ir.config_parameter']
        model_model_obj = self.env['ir.model']
        salt = config_parameter_obj.get_param("document.salt")
        if not salt:
            salt = uuid4()
            config_parameter_obj.set_param("document.salt", salt)
        model_id = model_model_obj.search([('model', '=', c_model)])
        secret = str(model_id.id) + str(salt)
        key = secret[:16].encode('utf-8')
        return key

    @api.model
    def encrypt_with_common_cipher(self, cleartext):
        common_cipher = self.get_common_cipher()
        clear_text_length = len(cleartext)
        next_multiple_of_16 = 16 * math.ceil(clear_text_length / 16)
        padded_clear_text = cleartext.rjust(next_multiple_of_16)
        raw_ciphertext = common_cipher.encrypt(padded_clear_text.encode('utf-8'))
        return base64.b64encode(raw_ciphertext)

    @api.model
    def decrypt_with_common_cipher(self, ciphertext):
        common_cipher = self.get_common_cipher()
        raw_ciphertext = base64.b64decode(ciphertext)
        decrypted_message_with_padding = common_cipher.decrypt(raw_ciphertext).decode('utf-8').strip()
        return decrypted_message_with_padding

    def _save_document(self):
        for document in self:
            document.document = document.encrypt_with_common_cipher(document.document_info)

    def _decrypt_document(self):
        for document in self:
            if document.document:
                value = document.decrypt_with_common_cipher(document.document)
                document.document_info = value
            else:
                document.document_info = ""
