odoo.define('bi_pos_bank_charges.PaymentScreen', function(require){
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const rpc = require('web.rpc');

    const BiPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            setup() {
				super.setup();
            }

           	async click_back(){
				let self = this;

				let orderlines = this.currentOrder.get_orderlines()

                if(orderlines){
                    const result = orderlines.filter(isBankCharge);
                    function isBankCharge(line) {
                      	return line.is_bankCharge == true;
                    }

                    if(result.length > 0){
                        const { confirmed } = await this.showPopup('ConfirmPopup', {
							title: self.env._t('Cancel Payment ?'),
							body: self.env._t('If you go back to product screen bank charge line will be remove'),
						});
						if (confirmed) {
							const BnkPayment = this.paymentLines.filter(isBankChargePayment);

		                    function isBankChargePayment(line) {
		                      	self.currentOrder.remove_paymentline(line)
		                    }
							
		                    this.currentOrder.remove_orderline(result[0])
							self.showScreen('ProductScreen');
						}
                    }else{
                    	self.showScreen('ProductScreen');
                    }
                }
			}

			deletePaymentLine(event) {
	            super.deletePaymentLine(event)

	            let orderlines = this.currentOrder.get_orderlines()
	            if(this.paymentLines.length == 0){
	                if(orderlines){
	                    const result = orderlines.filter(isBankCharge);
	                    function isBankCharge(line) {
	                      	return line.is_bankCharge == true;
	                    }
	                    if(result.length > 0){
	                    	this.currentOrder.remove_orderline(result[0])
	                    }
	                }
	            }else{
		            const BnkPayment = this.paymentLines.filter(isBankChargePayment);
		            function isBankChargePayment(line) {
		                return line.payment_method.is_bank_charge == true
		            }
		            if(BnkPayment.length == 0){
		            	const result = orderlines.filter(isBankCharge);

	                    function isBankCharge(line) {
	                      	return line.is_bankCharge == true;
	                    }

	                    if(result.length > 0){
	                    	this.currentOrder.remove_orderline(result[0])
	                    }
		            }
	            }
	        }


            _updateSelectedPaymentline() {
	            if (this.paymentLines.every((line) => line.paid)) {
	                this.currentOrder.add_paymentline(this.payment_methods_from_config[0]);
	            }
	            if (!this.selectedPaymentLine) return; // do nothing if no selected payment line
	            // disable changing amount on paymentlines with running or done payments on a payment terminal
	            const payment_terminal = this.selectedPaymentLine.payment_method.payment_terminal;
	            if (
	                payment_terminal &&
	                !['pending', 'retry'].includes(this.selectedPaymentLine.get_payment_status())
	            ) {
	                return;
	            }
	            if (NumberBuffer.get() === null) {
	                this.deletePaymentLine({ detail: { cid: this.selectedPaymentLine.cid } });
	            } else {
	            	var amount = NumberBuffer.getFloat()
	                this.selectedPaymentLine.set_amount(amount);

	                var pay_method = this.selectedPaymentLine.payment_method
	                if (pay_method.cahrges_type == "percentage"){

	                    var bank_charge_amount = ((pay_method.cahrges_amount * amount)/100)
	                    this.selectedPaymentLine.set_curamount(bank_charge_amount);
	                    
	                }
	            }
	        }

	        async _finalizeValidation() {

	        	await this.currentOrder.set_bnk_chrg(await this.currentOrder.get_total_bank_charge());
	            super._finalizeValidation();
	        }
            
            addNewPaymentLine({ detail: paymentMethod }) {
	            // original function: click_paymentmethods
	            let result = this.currentOrder.add_paymentline(paymentMethod);


	            if (result){
	            	if (paymentMethod.cahrges_type == "percentage"){
	                    var bank_charge_amount = result.get_amount()

	                    bank_charge_amount = ((paymentMethod.cahrges_amount * bank_charge_amount)/100)
	                    this.selectedPaymentLine.set_curamount(bank_charge_amount);
	                    var order = this.env.pos.get_order()
	                }
	                NumberBuffer.reset();
	                return true;
	            }
	            else{
	                var bank_charge_prod_id = this.env.pos.db.product_by_id[paymentMethod.bank_charge_prod_id[0]];
	                
		            if(bank_charge_prod_id){
		            	this.showPopup('ErrorPopup', {
		                    title: this.env._t('Error'),
		                    body: this.env._t('There is already an electronic payment in progress.'),
		                });
		                return false;
		            }else{
		                this.showPopup('ErrorPopup', {
		                    title: 'Bank Cahrge Product',
		                    body: 'Bank charge product is not available in pos..!!',
		                });
		                return false
		            }
	            }
        	}
    };

    Registries.Component.extend(PaymentScreen, BiPaymentScreen);

    return PaymentScreen;

});
