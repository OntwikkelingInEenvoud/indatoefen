# -*- coding: utf-8 -*-
{
	'name': "oi1_account_move_vat_shifted",

	'summary': """
	   Vat shifted for werkstandby
        """,

	'description': """
          
    """,

	'author': 'OntwikkelingInEenvoud (Remko Strating)',
	'website': "http://www.oi1.nl",

	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
	# for the full list
	'category': 'Tools',
	'version': '0.1',
	'license': 'GPL-3',

	# any module necessary for this one to work correctly
	'depends': ['base', 'account', 'sale_management', 'contacts'],

	# always loaded
	'data': [
		# 'security/ir.model.access.csv',
		'data/vat.xml',
		'views/res_partner_form.xml',
		'views/sale_order.xml',

	],
	# only loaded in demonstration mode
	'demo': [
		'demo/demo.xml',
	],
}