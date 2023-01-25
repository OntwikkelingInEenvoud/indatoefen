# -*- coding: utf-8 -*-
{
    'name': "oi1_import_excel_configuration",

    'summary': """
        This module makes a dynamic configuration of importing of Excel files in Odoo possible
        """,

    'description': """
       
    """,

    'author': "OntwikkelingInEenvoud B.V.",
    'website': "http://www.oi1.nl",
    'license': 'GPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Base',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates/templates.xml',    
        'views/import_excel.xml',          
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
