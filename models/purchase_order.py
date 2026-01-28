from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError, UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    lc_count = fields.Integer(compute='_compute_lc_count')

    def _compute_lc_count(self):
        for record in self:
            linked_lcs = self.env['lc.management'].search([('purchase_order_ids', 'in', record.id)])
            record.lc_count = len(linked_lcs)

    def action_view_lc_requests(self):
        self.ensure_one()
        linked_lc_ids = self.env['lc.management'].search([('purchase_order_ids', 'in', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'LC Requests',
            'res_model': 'lc.management',
            'view_mode': 'list,form',
            'domain': [('id', 'in', linked_lc_ids)],
            'context': {'create': False},
            'target': 'current',
        }

    def _check_lc_request_state(self, action_name):
        """
        Helper method to check if the PO is linked to an LC request 
        that is already processed (beyond draft or cancel).
        """
        for po in self:
            linked_lcs = self.env['lc.management'].search([
                ('purchase_order_ids', 'in', po.id),
                ('status', 'not in', ['draft', 'cancelled'])
            ])

            if linked_lcs:
                lc_numbers = ", ".join(linked_lcs.mapped('lc_number'))
                raise ValidationError(_(
                    "You cannot %s this Purchase Order (%s) because it is linked to "
                    "the following active LC Request(s): %s. "
                    "Please cancel or reset those LC requests to draft before proceeding."
                ) % (action_name, po.name, lc_numbers))

    def button_cancel(self):
        self._check_lc_request_state("cancel")
        return super(PurchaseOrder, self).button_cancel()

    def unlink(self):
        self._check_lc_request_state("delete")
        return super(PurchaseOrder, self).unlink()

    def _is_linked_to_approved_lc(self):
        return self.env['lc.management'].search_count([
            ('purchase_order_ids', 'in', self.id),
            ('status', '!=', ['draft', 'submitted'])
        ]) > 0

    def button_unlock(self):
        for record in self:
            if record._is_linked_to_approved_lc():
                # Check if current user is NOT an LC Manager
                if not self.env.user.has_group('lc_management.group_lc_manager'):
                    raise ValidationError(_(
                        "This PO is locked. "
                        "Only an LC Manager can unlock it."
                    ))
        return super(PurchaseOrder, self).button_unlock()



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _set_outdated_po_in_lcs(self):
        po_ids = self.mapped('order_id').ids
        if not po_ids:
            return


        lcs = self.env['lc.management'].search([
            ('purchase_order_ids', 'in', po_ids),
            ('status', 'in', ['draft', 'submitted']),
        ])

        if lcs:
            lcs.write({'is_outdated_po': True})

    def write(self, vals):
        res = super().write(vals)
        relevant = {'product_id', 'product_qty', 'price_unit'}
        if relevant.intersection(vals.keys()):
            self._set_outdated_po_in_lcs()
        return res

    def create(self, vals_list):
        records = super().create(vals_list)
        records._set_outdated_po_in_lcs()
        return records

    def unlink(self):
        lines = self
        res = super(PurchaseOrderLine, lines).unlink()
        lines._set_outdated_po_in_lcs()
        return res


