# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Bank Charges in POS',
    'version': '16.0.0.0',
    'category': 'Point of Sale',
    'summary': 'POS Extra Bank Charges on POS Extra Charges on POS credit card charges pos extra payment charges pos credit card extra charges point of sale extra bank charges on point of sale extra charges point of sale bank charges point of sales bank charge pos charges',
    'description' :"""
        
        POS Bank Charges Odoo App helps users to add bank charges in POS order payment. User can enable or disable POS bank charges in payment method then set bank charge amount in percentage. Bank charges should be automatically added while selecting configured payment method in POS and view bank changes in POS receipt, POS order and also in journal entry.

    """,
    'author': 'BrowseInfo',
    "price": 25,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.com',
    'depends': ['base','web','point_of_sale'],
    'data': [
        'views/bi_pos_config_view.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            "bi_pos_bank_charges/static/src/js/models.js",
            "bi_pos_bank_charges/static/src/js/PaymentScreen.js",
            "bi_pos_bank_charges/static/src/js/PaymentScreenStatus.js",
            'bi_pos_bank_charges/static/src/xml/paymentMethodButton.xml',
        ],
     },
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/xVfHKmhofqE',
    "images":['static/description/BankCharges-In-POS-Banner.gif'],
}
