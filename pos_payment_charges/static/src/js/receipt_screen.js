/** @odoo-module */

import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";

patch(ReceiptScreen.prototype, {
    get receipt() {
        const receipt = super.receipt;

        // Add payment charges information to receipt
        const order = this.pos.get_order();
        if (order && order.payment_charges) {
            receipt.payment_charges = order.payment_charges.map(charge => ({
                ...charge,
                product_name: this.pos.db.get_product_by_id(charge.product_id).display_name
            }));
        }

        return receipt;
    }
});