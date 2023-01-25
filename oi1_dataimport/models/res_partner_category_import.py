from odoo import models, fields, api, exceptions, _

class CategoryImport(models.TransientModel):

	_inherit = 'oi1_odooimport'

	def do_import_product_category(self, records):
		product_category_obj =  self.env['res.partner.category']
		for record in records:
			pc = False
			if 'x_prev_code' in record:
				pcs = product_category_obj.search([('x_prev_code','=', record['x_prev_code'])])
				if len(pcs) > 0:
					pc = pcs[0]
			if not pc and 'name' in record:
				pcs = product_category_obj.search([('name','=', record['name'])])
				if len(pcs) > 0:
					pc = pcs[0]
			if not pc and 'name' in record:
				pc = product_category_obj.create({'name' : record['name']})
			if not pc:
				print("No Product category found or created")
				continue;
			if 'x_prev_code' in record:
				pc.x_prev_code = record['x_prev_code']
			if 'name' in record:
				pc.name = record['name']

			Partner = False
			if 'partner_id' in record:
				Partners = self.env['res.partner'].browse([record['partner_id']])
				if len(Partners) > 0:
					Partner = Partners[0]
			if 'partner_id_x_prev_code' in record:
				Partners = self.env['res.partner'].search([('x_prev_code','=', record['partner_id_x_prev_code'])])
				if len(Partners) > 0:
					Partner = Partners[0]
			if Partner and pc:
			   Partner.category_id = [(4, pc.id)]
			if Partner:
			   print(Partner.name)
			self.env.cr.commit();
			print(pc.id)