# -*- coding: utf-8 -*-
{
	'name': "oi1_partner_search",

	'summary': """
	Adds extra options for searching to partners
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
	'depends': ['base', 'base_setup'],

	# always loaded
	'data': [
		# 'security/ir.model.access.csv',
		'views/res_config_settings.xml',
		'views/res_partner.xml',
		
	],
	# only loaded in demonstration mode
	'demo': [
		'demo/demo.xml',
	],
}