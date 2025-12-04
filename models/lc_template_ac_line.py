from odoo import models, fields


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
