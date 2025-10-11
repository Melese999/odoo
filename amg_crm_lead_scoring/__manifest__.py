{
    'name': 'AMG CRM Lead Scoring',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Custom lead scoring based on configurable rules.',
    'depends': ['crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_scoring_rule_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}