# -*- coding: utf-8 -*-
{
	'name': "oi1_free_worker_data_check",

	'summary': """
	Template project 
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
	'depends': ['base', 'oi1_free_worker', 'oi1_werkstandbij'],

	# always loaded
	'data': [
		'security/ir.model.access.csv',
		'views/oi1_free_worker.xml',
		'views/free_worker_data_check_wizard.xml',
		'views/mail_sign_agreement.xml',
		'views/mail_complete_nav.xml',
		'views/mail_send_iban.xml',
	],
	# only loaded in demonstration mode
	'demo': [
		'demo/demo.xml',
	],
}