# sale_mrp_location_tracking/__manifest__.py
{
    'name': 'Sale → MRPe: Location Tracking for Production (Sales → MO visibility)',
    'version': '1.0.0',
    'summary': 'Track plant/location on Sale Orders and propagate to Manufacturing Orders for worker visibility. Role-based control for changing location on sales.',
    'author': 'Melese Getaw',
    'license': 'LGPL-3',
    'category': 'Manufacturing',
    'depends': ['sale_management', 'mrp', 'stock'],
    'data': [
        'security/sale_mrp_security.xml',
        'views/res_users_views.xml',
        'views/sale_order_views.xml',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
}
