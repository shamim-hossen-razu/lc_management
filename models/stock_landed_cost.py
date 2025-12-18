from odoo import models, fields

class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    lc_management_id = fields.Many2one(
        'lc.management',
        string="LC Management",
        index=True,
        copy=False,
        ondelete='set null',
    )
