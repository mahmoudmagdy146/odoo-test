/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {

    async addNewPaymentLine({ detail: paymentMethod }) {
        const result = await super.addNewPaymentLine({ detail: paymentMethod });

        // Add charges after payment line is added
        if (paymentMethod && paymentMethod.charge_type !== 'none') {
            this.addPaymentCharges(paymentMethod);
        }

        return result;
    },

    addPaymentCharges(paymentMethod) {
        const order = this.pos.get_order();
        if (!order || !paymentMethod.charge_product_id) return;

        // Calculate charge amount
        const orderTotal = this.getOrderTotalWithoutCharges();
        let chargeAmount = 0;

        if (paymentMethod.charge_type === 'percentage') {
            chargeAmount = (orderTotal * paymentMethod.charge_amount) / 100;
        } else if (paymentMethod.charge_type === 'fixed') {
            chargeAmount = paymentMethod.charge_amount;
        }

        if (chargeAmount <= 0) return;

        // Get charge product
        const chargeProduct = this.pos.db.get_product_by_id(paymentMethod.charge_product_id[0]);
        if (!chargeProduct) return;

        // Remove existing charges for this payment method
        const existingCharges = order.get_orderlines().filter(line =>
            line.is_payment_charge && line.payment_method_id === paymentMethod.id
        );
        existingCharges.forEach(line => order.remove_orderline(line));

        // Add new charge line
        const chargeLine = order.add_product(chargeProduct, {
            quantity: 1,
            price: chargeAmount,
            merge: false
        });

        // Mark as payment charge
        chargeLine.is_payment_charge = true;
        chargeLine.payment_method_id = paymentMethod.id;

        // Store for backend
        if (!order.payment_charges) order.payment_charges = [];
        order.payment_charges = order.payment_charges.filter(c => c.payment_method_id !== paymentMethod.id);
        order.payment_charges.push({
            payment_method_id: paymentMethod.id,
            product_id: chargeProduct.id,
            amount: chargeAmount,
            tax_ids: chargeLine.get_applicable_taxes().map(tax => tax.id)
        });
    },

    getOrderTotalWithoutCharges() {
        const order = this.pos.get_order();
        let total = 0;
        for (const line of order.get_orderlines()) {
            if (!line.is_payment_charge) {
                total += line.get_price_with_tax();
            }
        }
        return total;
    },

    async deletePaymentLine({ detail: paymentLine }) {
        const paymentMethod = paymentLine.payment_method;

        // Remove associated charges
        if (paymentMethod && paymentMethod.charge_type !== 'none') {
            const order = this.pos.get_order();
            const chargeLines = order.get_orderlines().filter(line =>
                line.is_payment_charge && line.payment_method_id === paymentMethod.id
            );
            chargeLines.forEach(line => order.remove_orderline(line));

            if (order.payment_charges) {
                order.payment_charges = order.payment_charges.filter(
                    c => c.payment_method_id !== paymentMethod.id
                );
            }
        }

        return super.deletePaymentLine({ detail: paymentLine });
    }
});