{
    'name': 'POS Payment Method Charges',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'depends': ['point_of_sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_payment_method_view.xml',
        'views/pos_order_line_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_payment_charges/static/src/js/models.js',
            'pos_payment_charges/static/src/js/simple_payment_charges.js',
            'pos_payment_charges/static/src/js/receipt_screen.js',
            'pos_payment_charges/static/src/js/pos_store.js',
            'pos_payment_charges/static/src/xml/payment_templates.xml',
            'pos_payment_charges/static/src/xml/receipt_templates.xml',
            'pos_payment_charges/static/src/scss/payment_charges.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}