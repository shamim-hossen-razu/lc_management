from odoo import models, fields


class LcCurrencyRateLine(models.Model):
    _name = 'lc.currency.rate.line'
    _description = 'LC Currency Rate Line'

    lc_id = fields.Many2one('lc.management', string="LC")
    currency_id = fields.Many2one('res.currency', string="Currency")
    rate = fields.Float(string="Exchange Rate")
    amount = fields.Float(string="Amount in this Currency")
    amount_in_target = fields.Float(string="Amount in Target Currency")
    # target_currency_id = fields.Many2one('res.currency', related='lc_id.currency_id', string="Target Currency", store=True)