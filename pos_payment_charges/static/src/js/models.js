/** @odoo-module */

import { Order, Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

// Extend Orderline to handle payment charges
patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.is_payment_charge = options.is_payment_charge || false;
        this.payment_method_id = options.payment_method_id || null;
    },

    export_as_JSON() {
        const json = super.export_as_JSON();
        json.is_payment_charge = this.is_payment_charge;
        json.payment_method_id = this.payment_method_id;
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(json);
        this.is_payment_charge = json.is_payment_charge || false;
        this.payment_method_id = json.payment_method_id || null;
    }
});

// Extend Order to handle payment charges
patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.payment_charges = [];
    },

    export_as_JSON() {
        const json = super.export_as_JSON();
        json.payment_charges = this.payment_charges || [];
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(json);
        this.payment_charges = json.payment_charges || [];
    },

    add_product(product, options) {
        const line = super.add_product(product, options);

        // Set payment charge properties if provided in extras
        if (options && options.extras) {
            if (options.extras.is_payment_charge) {
                line.is_payment_charge = true;
                line.payment_method_id = options.extras.payment_method_id;
            }
        }

        return line;
    },

    // Override to include payment charges in total calculation
    get_total_with_tax() {
        const total = super.get_total_with_tax();
        return total;
    },

    // Get total without payment charges (for charge calculation)
    get_total_without_charges() {
        let total = 0;
        for (const line of this.get_orderlines()) {
            if (!line.is_payment_charge) {
                total += line.get_price_with_tax();
            }
        }
        return total;
    }
});