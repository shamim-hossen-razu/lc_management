from odoo import models, fields, api, _


class LcAdditionalCost(models.Model):
    _name = 'lc.additional.cost'
    _description = 'LC Additional Cost (Configuration)'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    lc_type = fields.Selection([
        ('revocable', 'Revocable LC'),
        ('irrevocable', 'Irrevocable LC'),
        ('import', 'Import LC'),
        ('export', 'Export LC'),
        ('confirmed', 'Confirmed LC'),
        ('unconfirmed', 'Unconfirmed LC'),
        ('at_sight', 'At Sight LC'),
        ('deferred', 'Deferred LC'),
        ('transferable', 'Transferable LC'),
        ('standby', 'Standby LC'),
        ('revolving', 'Revolving LC'),
        ('back_to_back', 'Back-to-Back LC'),
        ('foreign_back_to_back', 'Foreign Back-to-Back LC'),
        ('local_back_to_back', 'Local Back-to-Back LC'),
    ], string="LC Type")

    # Link to the auto-created product variant
    product_id = fields.Many2one(
        "product.product",
        string="Landed Cost Product",
        readonly=True,
        help="Service product automatically created for this additional cost.",
    )

    active = fields.Boolean(default=True)

    # Override create to auto-create product template and variant
    @api.model
    def create(self, vals):
        """
        When an Additional Cost is created:
        1) Create a service product.template with landed_cost_ok = True
        2) Link its first variant (product_variant_id) to product_id
        """
        name = vals.get("name") or "Additional Cost"

        # Create the product template
        template = self.env["product.template"].create({
            "name": name,
            "type": "service",
            "purchase_ok": True,
            "sale_ok": False,
            "landed_cost_ok": True,
        })

        # Set the product_id to the first variant of this template
        vals["product_id"] = template.product_variant_id.id

        # Create the additional cost record
        record = super(LcAdditionalCost, self).create(vals)
        return record

    # Override write to update product name if additional cost name changes
    def write(self, vals):
        res = super(LcAdditionalCost, self).write(vals)

        for rec in self:
            # Ensure product exists (if not, create it)
            if not rec.product_id:
                template = self.env['product.template'].create({
                    "name": rec.name,
                    "type": "service",
                    "purchase_ok": True,
                    "sale_ok": False,
                    "landed_cost_ok": True,
                })
                rec.product_id = template.product_variant_id.id

            # Update product name if additional cost name changed
            if "name" in vals and rec.product_id:
                rec.product_id.product_tmpl_id.name = rec.name

        return res
