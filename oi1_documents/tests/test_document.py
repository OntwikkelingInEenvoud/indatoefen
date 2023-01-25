# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
import json


@tagged('oi1_document_information', )
class TestDocumentInformation(TransactionCase):
    def setUp(self, *args, **kwargs):
        return super().setUp(*args, **kwargs)

    def test_create_encrypt_and_get_document_info(self):
        c_value = "secret_value"
        c_name = "Magnolia"
        c_dict = ' {"Document_1": {"Name":"' + c_name + '","Location":"Ayilon male","Amount":289,"Date":"5/5/18"}} '

        document_information_obj = self.env['oi1_document_information']
        document_information = document_information_obj.create({})
        document_information.document_info = c_value
        document_information = document_information_obj.browse([document_information.id])
        self.assertEqual(document_information.document_info, c_value)

        document_information.document_info = c_dict
        document_information = document_information_obj.browse([document_information.id])
        self.assertEqual(str(document_information.document_info), str(c_dict))

        dict_string = document_information.document_info
        dict = json.loads(dict_string)
        values = dict['Document_1']
        self.assertEqual(values['Name'], c_name)



