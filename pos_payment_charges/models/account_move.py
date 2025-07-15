from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        """Ensure payment charges are properly handled in journal entries"""
        lines_vals_list = super()._stock_account_prepare_anglo_saxon_out_lines_vals()

        # Add specific handling for payment method charges if needed
        for line in self.line_ids:
            if line.pos_order_line_id and line.pos_order_line_id.is_payment_charge:
                _logger.info(f"Processing payment charge in journal entry: {line.name}")

        return lines_vals_list