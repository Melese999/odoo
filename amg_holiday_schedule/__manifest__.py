{
    'name': 'AMG Holiday Schedules',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manage regional holiday calendars for KPI adjustments.',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/holiday_schedule_data.xml',
        'views/holiday_schedule_views.xml',
    ],
    'installable': True,
    'license':'LGPL-3'
}