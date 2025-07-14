odoo.define('bi_pos_bank_charges.PaymentScreenStatus', function(require){
    'use strict';

    const PaymentScreenStatus = require('point_of_sale.PaymentScreenStatus');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const rpc = require('web.rpc');

    const BiPaymentScreenStatus = (PaymentScreenStatus) =>
        class extends PaymentScreenStatus {
            setup() {
                super.setup();
            }

            get totalBankCharge() {
            	var totalBankChargeAmt = this.props.order.get_total_bank_charge()
            	let orderlines = this.props.order.get_orderlines()


                if(orderlines){
                    const result = orderlines.filter(isBankCharge);

                    function isBankCharge(line) {
                      	return line.is_bankCharge == true;
                    }

                    if(!this.props.order.finalized){
                        if(result.length > 0){
                            result[0].set_unit_price(totalBankChargeAmt)
                            result[0].price_manually_set = true;
                        }
                    }
                }
	            return this.env.pos.format_currency(totalBankChargeAmt);
	        }

	        get allTheTotal(){
	            let total = this.props.order.get_total_with_tax() + this.props.order.get_total_bank_charge()
	            return this.env.pos.format_currency(total)
	        }

    };

    Registries.Component.extend(PaymentScreenStatus, BiPaymentScreenStatus);
    return PaymentScreenStatus;
});