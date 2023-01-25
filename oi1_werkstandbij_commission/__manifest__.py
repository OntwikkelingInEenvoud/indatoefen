# -*- coding: utf-8 -*-
{
	'name': "oi1_werkstandbij_commission",

	'summary': """
	Module for determining the commissions within werkstandbij 
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
	'depends': ['base', 'oi1_free_worker', 'sale_management', 'timesheet_grid', 'contacts', 'project', 'account_accountant', 'sale_timesheet', 'oi1_text'],

	# always loaded
	'data': [
		'data/commission_role.xml',
		'data/text_type_data.xml',
		'security/ir.model.access.csv',
		'views/oi1_commission.xml',
		'views/res_partner.xml',
		'views/oi1_freeworker.xml',
		'views/sale_order.xml',
		'views/oi1_freeworkerpoule.xml',
		'views/oi1_sale_commission_unreserve_wizard.xml',
		'views/oi1_commission_payment.xml',
		'views/oi1_commission_role.xml',
		'views/oi1_commission_log.xml',
		'views/oi1_commission_rate_list.xml',
		'views/oi1_commission_payment_log.xml',
		'views/oi1_commission_payment_wizard.xml',
		'security/commission_rate.xml',
		'security/oi1_commission_payment.xml',
		'report/active_partner_commissions.xml',

	],
	# only loaded in demonstration mode
	'demo': [
		'demo/demo.xml',
	],
}