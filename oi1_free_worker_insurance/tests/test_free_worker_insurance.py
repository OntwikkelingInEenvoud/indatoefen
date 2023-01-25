from odoo.tests.common import TransactionCase, tagged


@tagged('test_insurance')
class TestFreeWorkerInsurance(TransactionCase):
	def setUp(self, *args, **kwargs):
		result = super().setUp(*args, **kwargs)

		hour_line_obj = self.env['account.analytic.line']
		free_worker_obj = self.env['oi1_free_worker']
		poule_obj = self.env['oi1_freeworkerpoule']

		free_workers = free_worker_obj.search([], limit=1)
		self.assertTrue(len(free_workers) > 0)
		self.free_worker = free_workers[0]

		poules = poule_obj.search([('sale_order_id', '!=', False)], limit=1)
		self.assertTrue(len(poules) > 0)
		poule = poules[0]

		self.sale_order = poule.sale_order_id
		self.assertTrue(self.sale_order.id)

		self.env.user.lang = False

		self.hour_line = hour_line_obj.create({
			'x_free_worker_id': self.free_worker.id,
			'x_sale_id': self.sale_order.id,
			'x_from_time': "17:00",
			'x_to_time': "22:00",
			'x_pause_time': "01:00",
			'project_id': poule.project_id.id,
			'unit_amount': 4.0,
			'x_rate': 15.00})


		return result

	def test_tariff_calculation(self):
		c_insurance_type_name = 'type_name'
		c_insurance_name = 'insurance_name'
		c_rate = 10
		c_perc = 10

		insurance_type_obj = self.env['oi1_insurance_type']
		insurance_obj = self.env['oi1_insurance']

		insurance_tariff_obj = self.env['oi1_insurance_tariff']
		insurance_package_obj = self.env['oi1_insurance_package']

		insurance_type = insurance_type_obj.create({'name': c_insurance_type_name})
		self.assertTrue(insurance_type.id)
		self.assertEqual(insurance_type.name, c_insurance_type_name)

		insurance = insurance_obj.create({'insurance_type_id': insurance_type.id,
										  'name': c_insurance_name
										  })
		self.assertTrue(insurance.id)
		self.assertEqual(insurance.name, c_insurance_name)

		insurance_tarif = insurance_tariff_obj.create({})
		insurance_tarif.rate = c_rate

		amount = insurance_tarif.calculate_amount(self.hour_line)
		self.assertEqual(amount, c_rate)

		insurance_tarif.rate = 0
		insurance_tarif.percentage = c_perc
		amount = insurance_tarif.calculate_amount(self.hour_line)
		check_insurance_amount = amount
		self.assertEqual(amount, self.hour_line.x_amount * c_perc/100)

		insurance_tarif.insurance_id = insurance

		insurance_tarif1 = insurance_tariff_obj.create({})
		insurance_tarif1.rate = c_rate

		amount = insurance_tarif1.calculate_amount(self.hour_line)
		self.assertEqual(amount, c_rate)
		insurance_tarif1.insurance_id = insurance
		check_insurance_amount = check_insurance_amount + amount
		self.assertTrue((len(insurance.insurance_tariff_ids) == 2))

		insurance_amount = insurance.calculate_amount(self.hour_line)
		self.assertEqual(check_insurance_amount, insurance_amount)

		insurance_package = insurance_package_obj.create({'code': 'code',
														  'description': 'test'})
		insurance_package.write({'insurance_ids': [(4, insurance.id)]})
		insurance_package_amount = insurance_package.calculate_amount(self.hour_line)
		self.assertEqual(insurance_package_amount, insurance_amount)

	def test_create_insurance_proces(self):
		c_insurance_type_name = 'type_name'
		c_insurance_name = 'insurance_name'

		insurance_schengen_type = self.env.ref('oi1_free_worker_insurance.oi1_insurance_schengen_type')

		insurance_type_obj =  self.env['oi1_insurance_type']
		insurance_obj = self.env['oi1_insurance']
		insurance_package_obj = self.env['oi1_insurance_package']
		insurance_premium_payment_obj = self.env['oi1_insurance_premium_payment']

		insurance_type = insurance_type_obj.create({'name': c_insurance_type_name})
		self.assertTrue(insurance_type.id)
		self.assertEqual(insurance_type.name, c_insurance_type_name)

		insurance = insurance_obj.create({'insurance_type_id': insurance_type.id,
										  'name': c_insurance_name
										  })
		self.assertTrue(insurance.id)
		self.assertEqual(insurance.name, c_insurance_name)

		insurance_schengens = insurance_obj.search([('insurance_type_id', '=', insurance_schengen_type.id)])
		self.assertFalse(len(insurance_schengens) == 0)
		insurance_schengen = insurance_schengens[0]
		self.assertTrue(insurance_schengen.insurance_type_id.id == insurance_schengen.id)

		insurance_package = insurance_package_obj.create({'code': 'code', 'description': 'description' })
		self.assertTrue(insurance_package.id)

		insurance_package.write({'insurance_ids': [(4,insurance_schengen.id)]})
		insurance_package.write({'insurance_ids': [(4, insurance.id)]})
		self.assertTrue(len(insurance_package.insurance_ids) == 2)

		self.sale_order.x_insurance_package_id = insurance_package

		insurance_premium_payment_obj.calculate_premium_payments_customer(self.hour_line)

		insurance_premium_payments = insurance_premium_payment_obj.search([('sale_id', '=', self.sale_order.id)])
		self.assertFalse(len(insurance_premium_payments) == 0)
		insurance_premium_payments = insurance_premium_payment_obj.search([('account_analytic_line_id', '=', self.hour_line.id)])
		self.assertFalse(len(insurance_premium_payments) == 0)
		insurance_premium_payments = insurance_premium_payment_obj.search(
			[('account_analytic_line_id', '=', self.hour_line.id)])
		self.assertFalse(len(insurance_premium_payments) == 0)




