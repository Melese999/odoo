{
    'name': 'KPI Management Framework',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Framework to define, assign, and track Key Performance Indicators.',
    'description': """
        This module provides the core framework for a comprehensive performance management system
        integrated within the CRM, as per AMG SRS requirements. It allows for the creation of
        KPI definitions and the assignment of targets to users and teams.
    """,
    'depends': [
        'crm',      # Essential for integrating with leads, opportunities, etc.
        'mail',     # For chatter and activity mixins
        'amg_holiday_schedule',  # For holiday calendar integration
        'crm_phonecall',
        'crm_telemarketing',
        'base_automation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml', # Add this new file
        'data/kpi_data.xml',
        'data/kpi_automated_actions.xml',
        'views/kpi_definition_views.xml',
        'views/kpi_target_views.xml',
        'views/kpi_history_views.xml', # Corrected filename
        'views/kpi_menus.xml',
        'views/kpi_reporting_views.xml',
        'views/kpi_dashboard_views.xml',
    ],
    'post_init_hook': '_link_automation_triggers_hook',
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}