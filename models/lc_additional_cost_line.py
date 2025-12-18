from odoo import models, fields


class LcManagementAdditionalCostLine(models.Model):
    _name = 'lc.additional.cost.line'
    _description = 'LC Additional Cost Line'

    lc_id = fields.Many2one('lc.management',string="LC",required=True, ondelete='cascade')
    additional_cost_id = fields.Many2one('lc.additional.cost',string="Additional Cost",required=True,)
    amount = fields.Monetary(string="Amount",currency_field='currency_id',required=True,)
    currency_id = fields.Many2one('res.currency',string="Currency",related='lc_id.currency_id',store=True,readonly=True,)
    note = fields.Char(string="Note")
