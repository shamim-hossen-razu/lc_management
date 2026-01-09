from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LcTemplateACLine(models.Model):
    _name = 'lc.template.ac.line'
    _description = 'LC Template Additional Cost Line'

    template_id = fields.Many2one(
        'lc.template',
        string="LC Template",
        required=True,
        ondelete='cascade',
    )

    additional_cost_id = fields.Many2one(
        'lc.additional.cost',
        string="Additional Cost",
        required=True,
    )

    amount = fields.Float(
        string="Amount",
    )

    note = fields.Char(string="Note")

    @api.constrains('additional_cost_id', 'amount')
    def _check_unique_cost_per_amount(self):
        for line in self:
            if not line.template_id:
                continue

            duplicate_lines = line.template_id.ac_template_line_ids.filtered(
                lambda l: l.additional_cost_id == line.additional_cost_id
                          and l.amount == line.amount
            )

            if len(duplicate_lines) > 1:
                raise ValidationError(_(
                    "The Additional Cost '%s' with amount %s "
                    "already exists in this template. You can add the same cost again "
                    "only if the amount is different."
                ) % (line.additional_cost_id.display_name, line.amount))
