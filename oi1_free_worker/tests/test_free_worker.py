# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
import datetime

@tagged('test_free_worker')
class TestFreeWorker(TransactionCase):
	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)
		self.env.user.lang = False
		return result

	def test_create_free_worker(self):
		free_worker_obj = self.env['oi1_free_worker']
		res_partner_bank_obj = self.env['res.partner.bank']

		free_worker = free_worker_obj.create({'x_name': 'tests'})
		self.assertEqual(free_worker.x_name, 'tests')
		free_worker.write({'x_name': 'test1'})
		self.assertEqual(free_worker.display_name, 'test1')
		self.assertTrue(free_worker.freeworker_code)
		self.assertNotEqual(free_worker.freeworker_code, '')
		self.assertTrue(free_worker.partner_id.x_is_freeworker)
		partner_id = free_worker.partner_id
		self.assertTrue(partner_id.id)
		self.assertEqual(free_worker.id, partner_id.x_freeworker_id.id)

		with self.assertRaises(Exception) as e:
			free_worker.freeworker_code = ''
		self.assertIn("freeworker code shouldn't be changed", str(e.exception))
		
		self.assertNotEqual(free_worker.freeworker_code, '')

		# A beneficiary should have a banking account
		beneficiary = free_worker.create({'x_name': 'test_parent'})
		res_partner_banks = res_partner_bank_obj.search([('partner_id', '=', beneficiary.partner_id.id)])
		self.assertEqual(len(res_partner_banks), 0)
		with self.assertRaises(ValidationError) as e:
			free_worker.commercial_partner_id = beneficiary.partner_id
		self.assertIn('has no banking account this is not allowed for a commercial partner', str(e.exception))

	def test_check_valid_registration_free_worker(self):
		c_valid_registration_date = datetime.date.today() + datetime.timedelta(days=1)
		c_invalid_registration_date = datetime.date.today() - datetime.timedelta(days=1)

		free_worker_obj = self.env['oi1_free_worker']
		free_worker = free_worker_obj.create({'name': 'test'})

		self.assertFalse(free_worker.has_a_valid_legitimation)
		free_worker.valid_registration_date = c_valid_registration_date
		self.assertTrue(free_worker.has_a_valid_legitimation)
		free_worker.valid_registration_date = c_invalid_registration_date
		self.assertFalse(free_worker.has_a_valid_legitimation)

	def test_create_bank_id(self):

		bank_obj = self.env['res.bank']
		free_worker_obj = self.env['oi1_free_worker']

		acc_number = 'NL70TRIO0123456789'
		bank_id = bank_obj.create({'name': 'test_bank'})

		free_worker = free_worker_obj.create({'x_name': 'tests'})
		free_worker.acc_number = acc_number
		free_worker.bank_id = bank_id
		self.assertTrue(free_worker.bank_partner_bank_id.id)
		self.assertEqual(len(free_worker.partner_id.bank_ids), 1)

		bank_ids = free_worker.partner_id.bank_ids
		self.assertEqual(bank_ids[0].partner_id.id, free_worker.partner_id.id)

		acc_number = 'BA391290079401028494'
		free_worker_ben = free_worker_obj.create({'x_name': 'test beneficiary'})
		free_worker_ben.acc_number = acc_number
		free_worker_ben.bank_id = bank_id
		self.assertTrue(free_worker_ben.bank_partner_bank_id.id)
		self.assertEqual(len(free_worker_ben.partner_id.bank_ids), 1)
		bank_ids = free_worker_ben.partner_id.bank_ids
		self.assertEqual(bank_ids[0].partner_id.id, free_worker_ben.partner_id.id)


