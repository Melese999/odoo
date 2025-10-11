{
    'name': 'Sales Order Bank Payments',
    'version': '1.0',
    'summary': 'Allow multiple bank payments with unique TT numbers on Sales Orders',
    'description': """
This module extends the Sales Order model to support multiple bank payments.
Each payment includes a Bank, TT Number (unique), and Amount. 
The Advance Payment field automatically sums up all payment amounts.
    """,
    'category': 'Sales',
    'author': 'Melese Getaw ',
    'depends': ['commission_system'],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
}
