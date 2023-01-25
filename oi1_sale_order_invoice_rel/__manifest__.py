# -*- coding: utf-8 -*-
{
    'name': "oi1_sale_order_invoice_rel",

    'summary': """
        Adds the option to link invoices directly to salesorders and not indirectly with the salesorderlines
       """,

    'description': """
        Long description of module's purpose
    """,

    'author': 'OntwikkelingInEenvoud (Remko Strating)',   
    'website': "http://www.wilhelmtell.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'GPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','sale', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',    
       
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}