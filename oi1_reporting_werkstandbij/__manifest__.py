# -*- coding: utf-8 -*-
{
	'name': "oi1_reporting_werkstandbij",

	'summary': """
		Reports for werkstandbij
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
	'depends': ['base','oi1_text'],

	# always loaded
	'data': [
		# 'security/ir.model.access.csv',
		'templates/external_layout.xml',
		'templates/external_invoice_layout.xml',
		'views/report_invoice.xml',
		'views/report_free_workers_specification.xml',
		'views/report_commission_payment.xml',
		'views/report_invoice_hours_specification.xml',
		
	],
	# only loaded in demonstration mode
	'demo': [
		'demo/demo.xml',
	],
}