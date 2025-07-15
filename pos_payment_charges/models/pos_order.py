from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _order_fields(self, ui_order):
        """Override to handle payment method charges"""
        order_fields = super()._order_fields(ui_order)

        # Process payment method charges
        if ui_order.get('payment_charges'):
            for charge in ui_order['payment_charges']:
                # Add charge as order line
                charge_line = {
                    'product_id': charge['product_id'],
                    'qty': 1,
                    'price_unit': charge['amount'],
                    'discount': 0,
                    'tax_ids': [[6, 0, charge.get('tax_ids', [])]],
                    'is_payment_charge': True,
                    'payment_method_id': charge['payment_method_id']
                }

                if 'lines' not in order_fields:
                    order_fields['lines'] = []

                order_fields['lines'].append([0, 0, charge_line])

        return order_fields

    def _prepare_invoice_vals(self):
        """Override to ensure charges are included in invoice"""
        vals = super()._prepare_invoice_vals()

        # Log payment method charges for debugging
        for line in self.lines:
            if hasattr(line, 'is_payment_charge') and line.is_payment_charge:
                _logger.info(f"Payment charge line in invoice: {line.product_id.name} - {line.price_unit}")

        return vals

    def _export_for_ui(self, order):
        """Export order data for UI including payment charges"""
        result = super()._export_for_ui(order)

        # Add payment charges to exported data
        payment_charges = []
        for line in order.lines:
            if line.is_payment_charge:
                payment_charges.append({
                    'payment_method_id': line.payment_method_id,
                    'product_id': line.product_id.id,
                    'amount': line.price_unit,
                    'tax_ids': line.tax_ids.ids
                })

        result['payment_charges'] = payment_charges
        return result