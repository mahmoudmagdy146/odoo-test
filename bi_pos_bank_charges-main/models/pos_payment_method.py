# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from collections import defaultdict
from odoo import api, fields, models, _
from odoo.http import request
from odoo.tools import float_is_zero, float_compare



class POSSession(models.Model):
	_inherit = 'pos.session'

	def _loader_params_pos_payment_method(self):
		result = super()._loader_params_pos_payment_method()
		result['search_params']['fields'].extend(['is_bank_charge','cahrges_type','cahrges_amount','bank_charge_prod_id'])
		return result



class POSorder(models.Model):
	_inherit = 'pos.order'

	bnk_charge = fields.Float("Bnk Charge")


	@api.model
	def _order_fields(self, ui_order):

		result = super(POSorder, self)._order_fields(ui_order)
		if ui_order['total_bank_charge']:
			result['amount_paid'] = ui_order['amount_paid']+ui_order['total_bank_charge']
			result['amount_total'] = ui_order['amount_total']+ui_order['total_bank_charge']
			result['bnk_charge'] = ui_order.get('total_bank_charge',0.0)
		return result


	@api.model
	def _payment_fields(self, order, ui_paymentline):
		result = super(POSorder, self)._payment_fields(order, ui_paymentline)
		if(ui_paymentline['currency_amount']):
			amount = ui_paymentline['amount'] or 0.0
			bnkCharge = ui_paymentline['currency_amount']
			result['amount'] = (amount + bnkCharge)
			result['bnk_charge'] = bnkCharge

		return result


class ExchangeRate(models.Model):
	_inherit = "pos.payment"

	bnk_charge = fields.Float("Bank Charge")





class POSConfig(models.Model):
	_inherit = 'pos.payment.method'


	is_bank_charge = fields.Boolean("POS Bank Charges")

	journal_type = fields.Selection(string='Journal Type', related='journal_id.type', readonly=True)
	cahrges_type = fields.Selection([
		('percentage', 'Percentage'),
		], string="Bank Charge Type",default='percentage')

	cahrges_amount = fields.Float(string="Bank Charge Amount")

	bank_charge_prod_id = fields.Many2one('product.product', domain = [('type', '=', 'service'),
		('available_in_pos', '=', True)],string="Bank Charge Product")


	@api.onchange('journal_id')
	def onc_journal_id(self):
		for pm in self:
			pm.is_bank_charge = False