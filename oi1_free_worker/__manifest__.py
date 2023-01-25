# -*- coding: utf-8 -*-
{
	'name': "oi1_free_worker",

	'summary': """"
		Beheer gegevens van vrije werkers 
        """,

	'description': """
		Vrije werkers app voor het beheren en opslaan van de gegevens van vrije werkers.
        Deze module wordt gebruikt als een basis module voor de aanpassingen van Odoo voor Werkstandby
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
	'depends': ['project', 'base', 'mail', 'oi1_partner_contactdetails', 'account','base_address_extended', 'oi1_documents', 'oi1_text'],

	# always loaded
	'data': [
		'views/oi1_education.xml',
		'views/oi1_freeworkerpoule.xml',
		'views/oi1_language_level.xml',
		'views/oi1_experience.xml',
		'views/oi1_experience_level.xml',
		'views/oi1_level.xml',
		'views/free_worker.xml',
		'views/account_invoice.xml',
		'views/oi1_nationality.xml',
		'wizard/identification_data_wizard.xml',
		'data/identificationdocumenttype.xml',
		'data/sequence.xml',
		'security/ir.model.access.csv',
		'security/freeworkerpoule.xml',
		'security/freeworker.xml',
	],
	# only loaded in demonstration mode
	'demo': [
		'demo/freeworker_demo_data.xml',
	],
}