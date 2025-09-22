# -*- coding: utf-8 -*-
{
    'name': "encounter_visit",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['crm','mail','crm_lead_geolocation'],

    # always loaded
    'data': [
        'security/encounter_visit_rule.xml',
        'security/ir.model.access.csv',
        "views/encounter_visit_views.xml",
        "views/crm_lead_views.xml",
        "views/res_partner_views.xml",
        'data/sequence.xml',

    ],
        "assets": {
        "web.assets_backend": [
            "encounter_visit/static/src/js/auto_location.js",
        ],
    },
 
}

