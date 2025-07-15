from odoo import models, fields, api


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    charge_type = fields.Selection([
        ('none', 'No Charge'),
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ], string='Charge Type', default='none',
        help="Type of charge to apply for this payment method")

    charge_amount = fields.Float(
        string='Charge Amount',
        default=0.0,
        help='Charge amount (percentage or fixed amount based on charge type)'
    )

    charge_account_id = fields.Many2one(
        'account.account',
        string='Charge Account',
        domain=[('account_type', '=', 'income')],
        help='Account to record payment method charges'
    )

    charge_product_id = fields.Many2one(
        'product.product',
        string='Charge Product',
        domain=[('type', '=', 'service')],
        help='Product used for payment method charges'
    )

    @api.constrains('charge_amount', 'charge_type')
    def _check_charge_amount(self):
        for record in self:
            if record.charge_type == 'percentage' and record.charge_amount < 0:
                raise ValueError("Percentage charge cannot be negative")
            if record.charge_type == 'fixed' and record.charge_amount < 0:
                raise ValueError("Fixed charge cannot be negative")

    @api.model
    def get_payment_method_info(self):
        """Return payment method information for POS"""
        result = super().get_payment_method_info()
        for method in result:
            method.update({
                'charge_type': self.browse(method['id']).charge_type,
                'charge_amount': self.browse(method['id']).charge_amount,
                'charge_product_id': self.browse(method['id']).charge_product_id.id if self.browse(
                    method['id']).charge_product_id else False,
            })
        return result