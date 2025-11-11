# -*- coding: utf-8 -*-
{
    'name': "lc_management",

    'summary': "Manage the lifecycle of Letters of Credit across Inventory, Sales, Purchases, Accouting, and Contacts module.",

    'description': """
This module manages the full process of Letters of Credit (LC) used in trade operations. It allows tracking and controlling LCs for both sales and purchases, assigns roles to banks involved, and organizes all related documents. The module links with inventory, invoicing, and accounting to ensure smooth coordination across departments.
    """,

    'author': "BJIT Limited",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'purchase', 'stock', 'accountant', 'contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/lc_bank_role_data.xml',
        'data/lc_sequence.xml',
        'views/res_company_views.xml',
        'views/res_bank_views.xml',
        'views/lc_bank_role_views.xml',
        'views/lc_management_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

