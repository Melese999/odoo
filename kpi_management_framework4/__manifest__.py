{
    'name': 'KPI Management Framework',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Framework to define, assign, and track Key Performance Indicators.',
    'description': """
        This module provides a simplified KPI management system with two main KPI types:
        - Data Quality: Average of confirmation percentages for leads
        - Leads Registered: Count of leads registered by users
    """,
    'depends': [
        'crm',
        'mail',
        # 'amg_holiday_schedule',
        'sales_team',
        'crm_phonecall',
        'resource',
    ],
    'data': [
        'security/telemarketer_groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/telemarketer_users.xml',
        'data/kpi_data.xml',
        'views/kpi_definition_views.xml',
        'views/kpi_target_views.xml',
        'views/kpi_target_line_views.xml',
        'views/kpi_history_views.xml',
        'views/crm_phonecall_views.xml',

        #'views/telemarketing_confirmation_views.xml',
        'views/kpi_dashboard_views.xml',
        #'views/kpi_reporting_views.xml',
        'views/kpi_menus.xml',

    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}