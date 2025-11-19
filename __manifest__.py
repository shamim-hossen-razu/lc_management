# -*- coding: utf-8 -*-
{
    'name': "LC Management",
    'summary': "Manage Letters of Credit (LC) within Odoo",

    'description': """
        Custom module for managing LCs
    """,
    'author': "BJIT Limited",
    'license': 'LGPL-3',
    'website': "https://www.bjitgroup.com",
    'category': 'Uncategorized',
    'version': '18.0.1.0.0',
    'depends': ['base', 'sale_management', 'purchase', 'stock', 'accountant', 'contacts', 'documents'],

    'data': [
        'security/ir.model.access.csv',
        'data/lc_bank_role_data.xml',
        'data/lc_sequence.xml',
        'views/res_company_views.xml',
        'views/res_bank_views.xml',
        'views/lc_bank_role_views.xml',
        'views/lc_management_views.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],
}

