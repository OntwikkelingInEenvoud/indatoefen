# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('werkstandbij', 'test_partner_bank')
class TestPartnerBank(TransactionCase):

	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)
		self.env.user.lang = False
		return result

	def test_set_iban(self):
		partner_bank_obj = self.env['res.partner.bank']
		bank_obj = self.env['res.bank']
		partner_obj = self.env['res.partner']

		bank_id = bank_obj.create({'name': 'test_bank'})

		partner_bank_id1 = partner_bank_obj.search([('acc_number', '=','NL03NIET07052003451',)]
												   , limit=1)
		partner_bank_id1.unlink()
		partner_id = partner_obj.create({'name': 'test_bank_partner'})
		partner_id2 = partner_obj.create({'name': 'test_bank_partner2'})

		acc_number = 'NL26INGB5353131762'
		error_acc_number = 'NL03NIET07052003451'
		with self.assertRaises(ValidationError) as e:
			partner_bank_obj.create({'acc_number': error_acc_number,
			 						'partner_id': partner_id.id})
		self.assertIn('invalid Iban', str(e.exception))

		with self.assertRaises(ValidationError) as e:
			partner_bank_obj.create({'acc_number': acc_number,
														'partner_id': partner_id.id})
		self.assertIn('no bank', str(e.exception))

		partner_bank_id1 = partner_bank_obj.create({'acc_number': acc_number,
													'partner_id': partner_id.id,
													'bank_id': bank_id.id})

		with self.assertRaises(ValidationError) as e:
			partner_bank_obj.create({'acc_number': acc_number,
									'partner_id': partner_id2.id,
									 'bank_id': bank_id.id
									 })
		self.assertIn('has already Iban', str(e.exception))
