from odoo import models, fields, api


class LcPoCostLine(models.Model):
    _name = 'lc.po.cost.line'
    _description = 'LC PO-wise Additional Cost'

    lc_id = fields.Many2one(
        'lc.management',
        string="LC",
        required=True,
        ondelete='cascade',
    )

    purchase_id = fields.Many2one(
        'purchase.order',
        string="Purchase Order",
        required=True,
    )

    additional_cost_line_id = fields.Many2one(
        'lc.additional.cost.line',
        string="Additional Cost Line",
        required=True,
    )

    additional_cost_id = fields.Many2one(
        'lc.additional.cost',
        string="Additional Cost",
        related='additional_cost_line_id.additional_cost_id',
        store=True,
        readonly=True,
    )

    amount = fields.Monetary(
        string="Allocated Amount",
        currency_field='currency_id',
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='lc_id.currency_id',
        readonly=True,
        store=True,
    )

    quantity = fields.Float(
        string="Quantity",
        compute="_compute_po_summary",
        store=True,
    )
    current_cost = fields.Monetary(
        string="Current Cost",
        currency_field='currency_id',
        compute="_compute_po_summary",
        store=True,
    )
    weight = fields.Float(
        string="Weight",
        compute="_compute_po_summary",
        store=True,
    )
    volume = fields.Float(
        string="Volume",
        compute="_compute_po_summary",
        store=True,
    )

    @api.depends(
        'purchase_id',
        'purchase_id.order_line.product_qty',
        'purchase_id.order_line.price_subtotal',
        'purchase_id.order_line.product_id.weight',
        'purchase_id.order_line.product_id.volume',
    )
    def _compute_po_summary(self):
        for line in self:
            po = line.purchase_id
            qty = cost = weight = volume = 0.0
            for pol in po.order_line:
                q = pol.product_qty
                qty += q
                cost += pol.price_subtotal
                weight += (pol.product_id.weight or 0.0) * q
                volume += (pol.product_id.volume or 0.0) * q
            line.quantity = qty
            line.current_cost = cost
            line.weight = weight
            line.volume = volume
