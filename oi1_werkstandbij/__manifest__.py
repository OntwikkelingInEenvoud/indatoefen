# -*- coding: utf-8 -*-
{
	'name': "oi1_werkstandbij",

	'summary': """
        Adjustments for workstandby
       """,

	'description': """
        Long description of module's purpose
    """,

	'author': 'OntwikkelingInEenvoud (Remko Strating)',
	'website': "http://www.oi1.nl",

	'category': 'Uncategorized',
	'version': '0.1',
	'license': 'GPL-3',

	# any module necessary for this one to work correctly
	'depends': ['base', 'l10n_nl', 'project', 'contacts', 'account', 'sale_management', 'timesheet_grid','oi1_free_worker',
				'sale_timesheet', 'account_accountant',
				'oi1_reporting_werkstandbij', 'oi1_werkstandbij_commission', 'account_sepa'],

	# always loaded
	'data': [
		'views/data.xml',
		'security/ir.model.access.csv',
		'views/res_partner.xml',
		'views/oi1_freeworkerpoule.xml',
		'views/sale_order.xml',
		'views/account_analytic_line.xml',
		'views/oi1_freeworker.xml',
		'views/account_move.xml',
		'views/account_invoice_payment_wsb.xml',
		'views/account_journal.xml',
		'views/oi1_commission_invoice_helper.xml',
		'views/account_payment.xml',
		'views_wizards/oi1_agreehourline_wizard.xml',
		'views_wizards/oi1_invoice_wizard.xml',
		'views_wizards/oi1_cancelagreehourline_wizard.xml',
		'views_wizards/oi1_invoice_refund_hour_wizard.xml',
		'data/transport.xml',
		'data/product_template.xml',
		'data/level.xml',
		'data/resource_calendar_attendance_workday_part.xml',
		'data/commissions.xml',
	],
	# only loaded in demonstration mode
	'demo': [
		'demo/oi1_freeworkerpoule.xml',
		'demo/company.xml',
		'demo/account_account.xml',
		'demo/sale_commission.xml',
		'demo/account_analytic_line.xml',

	],
	'qweb': [
		# 'templates/template.xml',

	],
}
