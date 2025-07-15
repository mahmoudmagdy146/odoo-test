from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    is_payment_charge = fields.Boolean(
        string='Is Payment Charge',
        default=False,
        help='Indicates if this line is a payment method charge'
    )

    payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Payment Method',
        help='Payment method that generated this charge'
    )