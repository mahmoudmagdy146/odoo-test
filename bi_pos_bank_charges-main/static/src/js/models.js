odoo.define('bi_pos_bank_charges.models', function (require) {
	"use strict";
	
	
	var utils = require('web.utils');
	var round_pr = utils.round_precision;
	var { Order, Orderline,Payment } = require('point_of_sale.models');
	const Registries = require('point_of_sale.Registries');


	const PosOrder = (Order) => class PosOrder extends Order {
	    constructor(obj, options) {
		    super(...arguments);		      
		    this.total_bank_charge = this.total_bank_charge || 0;
	  	}

	  	set_bnk_chrg (charge) {
			this.total_bank_charge = charge
		}

		get_total_bank_charge() {
			var self = this
	        return round_pr(this.paymentlines.reduce((function(sum, paymentLine) {
	            if (paymentLine.is_done()) {
	            	if(paymentLine.payment_method.is_bank_charge){
	                	sum += paymentLine.get_curamount();
	            	}
	            }
	            return sum;
	        }), 0), this.pos.currency.rounding);
	    }

	    get_total_without_tax() {
	        return round_pr(this.orderlines.reduce((function(sum, orderLine) {
	            if(orderLine.is_bankCharge){
	                return sum + 0
	            }else{
	                return sum + orderLine.get_price_without_tax();
	            }
	        }), 0), this.pos.currency.rounding);
	    }

	    get_total_with_tax() {
	        return round_pr(this.orderlines.reduce((function(sum, orderLine) {
	            if(orderLine.is_bankCharge){
	                return sum + 0
	            }else{
	                return sum + orderLine.get_price_with_tax();
	            }
	        }), 0), this.pos.currency.rounding);
	    }

	    add_paymentline(payment_method) {
	        this.assert_editable();
	        if (this.electronic_payment_in_progress()) {
	            return false;
	        } else {
                var bank_charge_prod_id = this.pos.db.product_by_id[payment_method.bank_charge_prod_id[0]];
                

	            if(payment_method.is_bank_charge == true){

	                if(bank_charge_prod_id){


	                	var newPaymentline = Payment.create({},{order: this, payment_method:payment_method, pos: this.pos});
			            this.paymentlines.add(newPaymentline);
			            this.select_paymentline(newPaymentline);
			            if(this.pos.config.cash_rounding){
			              this.selected_paymentline.set_amount(0);
			            }
			            newPaymentline.set_amount(this.get_due());

			            if (payment_method.payment_terminal) {
			                newPaymentline.set_payment_status('pending');
			            }

			            let orderlines = this.get_orderlines()

                        if(orderlines){
                            const result = orderlines.filter(isBankCharge);

                            function isBankCharge(line) {
                              	return line.is_bankCharge == true;
                            }
                            if(result.length == 0){
                                var line = Orderline.create({}, {pos: this.pos, order: this, product: bank_charge_prod_id});            
                                line.set_is_bankCharge(true)
                                line.set_quantity(1)
                                this.orderlines.add(line);
                            }
                        } 

			            return newPaymentline;	
	                }else{
	                	return false
	                }
	            }else{
	            	var newPaymentline = Payment.create({},{order: this, payment_method:payment_method, pos: this.pos});
		            newPaymentline.set_amount(this.get_due());
		            this.paymentlines.add(newPaymentline);
		            this.select_paymentline(newPaymentline);
		            if(this.pos.config.cash_rounding){
		              this.selected_paymentline.set_amount(0);
		              this.selected_paymentline.set_amount(this.get_due());
		            }

		            if (payment_method.payment_terminal) {
		                newPaymentline.set_payment_status('pending');
		            }
		            return newPaymentline;
	            }

	            
	        }
	    }

	    export_for_printing() {
			const json = super.export_for_printing(...arguments);
			json.total_bank_charge = this.get_total_bank_charge()|| [];
			return json;
		}
	  	
		init_from_JSON(json) {
			super.init_from_JSON(...arguments);
			this.total_bank_charge = json.total_bank_charge;
		}
		export_as_JSON() {
			const json = super.export_as_JSON(...arguments);
			json.total_bank_charge = this.get_total_bank_charge();
			return json;
		}
	}
	Registries.Model.extend(Order, PosOrder);



	const CustomOrderLine = (Orderline) => class CustomOrderLine extends Orderline {
        constructor(obj, options) {
            super(...arguments);
            this.is_bankCharge = this.is_bankCharge || false;
        }
        set_is_bankCharge(is_bankCharge){
			this.is_bankCharge = is_bankCharge;
		}
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.is_bankCharge = this.is_bankCharge || false;
            return json;
        }
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.is_bankCharge = json.is_bankCharge ||false;
        }
        export_for_printing() {
            const json = super.export_for_printing(...arguments);
            json.is_bankCharge = this.is_bankCharge || false;
            return json;
        }

    }
    Registries.Model.extend(Orderline, CustomOrderLine);


    const PaymentLine = (Payment) => class PaymentLine extends Payment {
        constructor(obj, options) {
			super(...arguments);
            this.currency_amount = this.currency_amount || 0.0;
			this.currency_symbol = this.currency_symbol || this.pos.currency.symbol;
        }

        set_curamount(currency_amount){
			this.currency_amount = currency_amount;
		}
		
		get_curamount() {
			return this.currency_amount
		}

		set_currency_symbol(currency_symbol){
			this.currency_symbol = currency_symbol;
			this.trigger('change',this);
		}
        
        init_from_JSON(json){
            super.init_from_JSON(...arguments);
            this.currency_amount = json.currency_amount || 0.0;
			this.currency_symbol = json.currency_symbol || this.pos.currency.symbol;
        }

        export_as_JSON(){
            const json = super.export_as_JSON(...arguments);
            json.currency_amount = this.currency_amount || 0.0;
			json.currency_symbol = this.currency_symbol || this.pos.currency.symbol;
            return json;
        }

        export_for_printing() {
            const json = super.export_for_printing(...arguments);
            json.currency_amount = this.currency_amount || 0.0;
			json.currency_symbol = this.currency_symbol || this.pos.currency.symbol;
            return json;
        }

    }
    Registries.Model.extend(Payment, PaymentLine);
});