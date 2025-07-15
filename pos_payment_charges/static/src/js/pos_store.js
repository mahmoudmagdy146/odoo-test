/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    // Load payment method charge fields
    async _loadPosData() {
        const loaded = await super._loadPosData();

        // Ensure payment method model includes charge fields
        const paymentMethods = this.models['pos.payment.method'];
        if (paymentMethods) {
            for (const method of Object.values(paymentMethods)) {
                method.charge_type = method.charge_type || 'none';
                method.charge_amount = method.charge_amount || 0;
                method.charge_account_id = method.charge_account_id || false;
                method.charge_product_id = method.charge_product_id || false;
            }
        }

        return loaded;
    }
});
