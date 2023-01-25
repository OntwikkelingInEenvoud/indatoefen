# -*- coding: utf-8 -*-
{
	'name': "oi1_text",

	'summary': """
        Provides the option to add standaard text fields to reports and calculates the standard fields within reporting. 
        """,

	'description': """
          
    """,

	'author': 'OntwikkelingInEenvoud (Remko Strating)',
	'website': "http://www.oi1.nl",

	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
	# for the full list
	'category': 'Tools',
	'version': '0.4',
	'license': 'GPL-3',

	# any module necessary for this one to work correctly
	'depends': ['base', 'sale_management'],

	# always loaded
	'data': [
		'security/ir.model.access.csv',
		'data/default_page_formats.xml',
		'views/oi1_text.xml',
		'views/oi1_text_type.xml',
		'data/oi1_text_default_data.xml',
		'views/res_partner.xml',
		'views/res_company_form.xml',
		'views/account_invoice.xml',

	],
	# only loaded in demonstration mode
	'demo': [
		'demo/demo.xml',
	],
}