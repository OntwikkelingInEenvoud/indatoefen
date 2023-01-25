# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('test_convert_free_worker_identification_data')
class TestFreeWorker(TransactionCase):
	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)
		self.env.user.lang = False
		return result

	def test_convert_free_worker_identification_data(self):
		convert_obj =  self.env['convert_free_worker_identification_data']
		convert_obj.convert_identification_data()
		self.assertEqual(1,2)
