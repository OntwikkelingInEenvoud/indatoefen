# -*- coding: utf-8 -*-
{
    'name': "oi1_partner_contactdetails",

    'summary': """
        This module will add extra fields to the table res partner where extra information is visible
        """,

    'description': """
       
    """,

    'author': 'OntwikkelingInEenvoud (Remko Strating)',   
    'website': "http://www.wilhelmtell.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Base',
    'version': '0.1',
    'license': 'GPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'templates/templates.xml',  
        'views/res_partner.xml',
        'views/res_user.xml',
        ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
