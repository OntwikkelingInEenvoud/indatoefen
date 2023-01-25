# -*- coding: utf-8 -*-
{
	'name': "oi1_free_worker_insurance",

	'summary': """
		Within this app the insurance of the free workers are handled.  
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
	'depends': ['base', 'oi1_free_worker', 'oi1_werkstandbij', 'oi1_werkstandbij_commission'],

	# always loaded
	'data': [
		'data/data_insurance_type.xml',
		'data/data_insurance.xml',
		'data/data_res_group.xml',
		'security/ir.model.access.csv',
		'views/oi1_free_worker.xml',
		'views/oi1_insurance_type.xml',
		'views/oi1_insurance.xml',
		'views/oi1_insurance_polis.xml',
		'views/oi1_insurance_tariff.xml',
		'views/oi1_insurance_package.xml',
		'views/res_partner.xml',
		'views/sale_order.xml',
	],
	# only loaded in demonstration mode
	'demo': [
		'demo/demo.xml',
	],
}