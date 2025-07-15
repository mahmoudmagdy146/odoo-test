/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.pos = useService("pos");
    },

    async addNewPaymentLine({ detail: paymentMethod }) {
        const result = await super.addNewPaymentLine({ detail: paymentMethod });

        // Calculate and add payment charges after adding payment line
        if (paymentMethod && paymentMethod.charge_type !== 'none') {
            this._calculatePaymentCharges(paymentMethod);
        }

        return result;
    },

    _calculatePaymentCharges(paymentMethod) {
        if (!paymentMethod || paymentMethod.charge_type === 'none') {
            return;
        }

        const order = this.pos.get_order();
        if (!order) return;

        // Get the subtotal before charges
        const orderTotal = order.get_total_with_tax();
        let chargeAmount = 0;

        if (paymentMethod.charge_type === 'percentage') {
            chargeAmount = (orderTotal * paymentMethod.charge_amount) / 100;
        } else if (paymentMethod.charge_type === 'fixed') {
            chargeAmount = paymentMethod.charge_amount;
        }

        if (chargeAmount > 0) {
            this._addChargeToOrder(paymentMethod, chargeAmount);
        }
    },

    _addChargeToOrder(paymentMethod, chargeAmount) {
        const order = this.pos.get_order();
        const chargeProduct = this.pos.db.get_product_by_id(paymentMethod.charge_product_id[0]);

        if (!chargeProduct) {
            console.error('Charge product not found for payment method:', paymentMethod.name);
            return;
        }

        // Remove existing charge for this payment method
        const existingCharges = order.get_orderlines().filter(line =>
            line.is_payment_charge && line.payment_method_id === paymentMethod.id
        );

        existingCharges.forEach(line => order.remove_orderline(line));

        // Add new charge line
        const chargeLine = order.add_product(chargeProduct, {
            quantity: 1,
            price: chargeAmount,
            merge: false,
            extras: {
                is_payment_charge: true,
                payment_method_id: paymentMethod.id
            }
        });

        // Store charge information for backend processing
        if (!order.payment_charges) {
            order.payment_charges = [];
        }

        order.payment_charges.push({
            payment_method_id: paymentMethod.id,
            product_id: chargeProduct.id,
            amount: chargeAmount,
            tax_ids: chargeLine.get_applicable_taxes().map(tax => tax.id)
        });
    },

    async _finalizeValidation() {
        // Ensure all payment charges are calculated before finalizing
        const order = this.pos.get_order();
        const paymentLines = order.get_paymentlines();

        paymentLines.forEach(paymentLine => {
            if (paymentLine.payment_method.charge_type !== 'none') {
                this._calculatePaymentCharges(paymentLine.payment_method);
            }
        });

        return super._finalizeValidation();
    },

    // Remove payment charges when payment line is removed
    async deletePaymentLine(event) {
        const { detail: paymentLine } = event;
        const paymentMethod = paymentLine.payment_method;

        // Remove associated charges
        if (paymentMethod && paymentMethod.charge_type !== 'none') {
            const order = this.pos.get_order();
            const chargeLines = order.get_orderlines().filter(line =>
                line.is_payment_charge && line.payment_method_id === paymentMethod.id
            );

            chargeLines.forEach(line => order.remove_orderline(line));

            // Remove from payment_charges array
            if (order.payment_charges) {
                order.payment_charges = order.payment_charges.filter(
                    charge => charge.payment_method_id !== paymentMethod.id
                );
            }
        }

        return super.deletePaymentLine(event);
    }
});