from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LcManagementAdditionalCostLine(models.Model):
    _name = 'lc.additional.cost.line'
    _description = 'LC Additional Cost Line'

    lc_id = fields.Many2one('lc.management',string="LC",required=True, ondelete='cascade')
    additional_cost_id = fields.Many2one('lc.additional.cost',string="Additional Cost",required=True,)
    amount = fields.Monetary(string="Amount",currency_field='currency_id',required=True,)
    currency_id = fields.Many2one('res.currency',string="Currency",related='lc_id.currency_id',store=True,readonly=True,)
    note = fields.Char(string="Note")

    @api.constrains('lc_id', 'additional_cost_id', 'amount')
    def _check_unique_cost_and_amount(self):
        for line in self:
            if not line.lc_id or not line.additional_cost_id:
                continue

            duplicate = self.search([
                ('id', '!=', line.id),
                ('lc_id', '=', line.lc_id.id),
                ('additional_cost_id', '=', line.additional_cost_id.id),
                ('amount', '=', line.amount)
            ], limit=1)

            if duplicate:
                raise ValidationError(_(
                    "The Additional Cost '%s' with the amount %s %s "
                    "already exists for this LC. You can only add the same cost category "
                    "twice if the amount is different."
                ) % (line.additional_cost_id.display_name, line.amount, line.currency_id.symbol))
