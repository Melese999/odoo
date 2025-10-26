# -*- coding: utf-8 -*-
{
    'name': "Commission System",

    'summary': "Automate the process of calculating, tracking, and managing commissions",

    'description': """
    A comprehensive software solution designed to streamline and automate the process of calculating, tracking, and managing
    commissions across various business models.
    """,

    'author': "Kibrom Mahari",
    'website': "https://www.amgholdingsplc.com",

    'category': 'SALE',
    'version': '0.1.1',
    'license': 'LGPL-3',

    'depends': ['board', 'base', 'crm', 'sale', 'account', 'contacts', 'product', 'web', 'uom', 'mrp', 'stock','sale_stock'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/favicon_template.xml',
        'views/account_move.xml',
        'views/res_partner_views.xml',
        # 'controllers/controllers.py',
        'data/cron.xml',
        'data/worksheet_status_data.xml',
        'data/cron_job.xml',
        'views/report_templates.xml',
        'views/reports.xml',
        'views/sale_order_views.xml',
        'views/sale_order_line_views.xml',
        'views/product_template_extend.xml',
        'views/mrp_production_view.xml',
        'views/mrp_production_views.xml',
        'views/production_report.xml',
        'views/production_wizard_views.xml',
        'reports/grouped_production_report.xml',
        'views/sales_sketch_views.xml',
        'views/sketch_wizard_views.xml',
        'views/commission_bill_summary_views.xml',
        'views/res_users_views.xml',
        # 'views/test.xml',
        # 'views/commission_sketch_wizard_view.xml',
        # 'views/assets.xml',
    ],

    'assets': {
        'web.assets_backend': [
            # CSS
            'commission_system/static/src/css/style.css',
            'commission_system/static/src/scss/sale_order_custom.scss',

            # JavaScript - load in correct order
            # 'commission_system/static/src/js/debug.js',
            # 'commission_system/static/src/js/main.js',
            'commission_system/static/src/js/commission_line_kanban.js',
            'commission_system/static/src/js/sketch_widget.js',

            # XML Templates
            'commission_system/static/src/xml/commission_line_kanban.xml',
            'commission_system/static/src/xml/sketch_widget.xml',
        ],
        'web.assets_frontend': [
            'commission_system/static/src/css/login_button_style.css',
            'commission_system/static/src/css/hide_powered_by.css',
        ],
    },

    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'icon': '/commission_system/static/description/icon.png',
}