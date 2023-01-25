# -*- coding: utf-8 -*-
{
    'name': "oi1_dataimport",

    'summary': """
        This module makes importing of data within odoo easy 
             """,

    'description': """
        Long description of module's purpose
    """,

    'author': 'OntwikkelingInEenvoud (Remko Strating)',   
    'website': "http://www.wilhelmtell.nl",
    'license': 'GPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'oi1_import_excel_configuration', 'product', 'contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/ExcelImportWizard.xml',
        'views/AccountAccountImport.xml', 
        'views/ResPartnerImport.xml',
        'views/ResPartnerCategoryImport.xml',
        'views/MailMessageImport.xml',
        'views/MailActivityImport.xml',
        'views/AttachmentImport.xml',
        'views/res_partner.xml', 
        'views/sequence.xml',
        
      
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}