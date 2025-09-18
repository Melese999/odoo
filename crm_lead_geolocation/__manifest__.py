{
    'name': 'CRM Lead Geolocation',
    'version': '1.0',
    'summary': 'Capture live GPS location on CRM Leads',
    'depends': ['crm','web','leaflet_map'],
    'data': [
        'security/groups.xml',
        'security/crm_lead_rule.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',


    ],
    'assets': {
        'web.assets_backend': [
            'crm_lead_geolocation/static/src/js/geo_capture.js',
        ],
    },
    'installable': True,
    'application': False,
}
