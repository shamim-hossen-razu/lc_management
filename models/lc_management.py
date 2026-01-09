from odoo import models, fields, api, _, tools
from datetime import date, timedelta
from odoo.exceptions import ValidationError, UserError

from markupsafe import Markup



class LcManagement(models.Model):
    _name = 'lc.management'
    _description = 'Letter of Credit Management'
    _rec_name = 'lc_number'
    _order = 'priority desc, create_date desc, id desc'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    # LC related basic information and its types
    lc_number = fields.Char(string="LC Number", readonly=True, copy=False, default='New')
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Urgent')], 'Priority', default='0', index=True)

    applicant_id = fields.Many2one('res.partner', string="Applicant", default=lambda self: self.env.user.partner_id, readonly=True, help="Buyer applying for the LC")
    applicant_company_id = fields.Many2one('res.company', string="Applicant Company", compute="_compute_applicant_company", store=True, readonly=True, help="Parent company of the logged-in user")

    beneficiary_company_id = fields.Many2one('res.partner', string="Beneficiary Company", domain=[('is_company', '=', True)], help="Company supplying the goods", tracking=True)
    beneficiary_id = fields.Many2one('res.partner', string="Beneficiary", domain=[], help="Individual contact under the selected company (Seller/Exporter)", tracking=True)

    issuing_bank_id = fields.Many2one('res.bank', string="Issuing Bank", help="Bank issuing the LC for the buyer", tracking=True)
    advising_bank_id = fields.Many2one('res.bank', string="Advising Bank", help="Bank advising the LC to the seller", tracking=True)

    amount = fields.Float(string="Amount", help="Total amount guaranteed by the LC", tracking=True)
    expiration_date = fields.Date(string="Expiration Date", help="Expiration date of the LC", tracking=True)


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
    ], string="LC Type", required=True, tracking=True)

    purchase_order_ids = fields.Many2many(
        'purchase.order',
        'lc_management_purchase_order_rel',
        'lc_id',
        'purchase_id',
        string='Purchase Orders', tracking=True
    )

    # Currency and finance information
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.ref('base.USD'), help="Currency of the LC amount", tracking=True)
    currency_rate = fields.Float(string="Currency Exchange Rate", tracking=True)
    margin_percentage = fields.Float(string="Margin Percentage", help="Margin required by the issuing bank", tracking=True)
    acc_name = fields.Char(string="Account Name", tracking=True)
    bank_account_id = fields.Many2one('res.partner.bank',string="Account No", help="Bank account number", tracking=True)

    # shipment information
    partial_shipment = fields.Boolean(string="Partial Shipment Allowed", tracking=True)
    transshipment = fields.Boolean(string="Transshipment Allowed", tracking=True)
    required_documents = fields.Html(string="Required Documents", help="Invoice, Packing List, B/L, Insurance, etc.", tracking=True)
    date_of_issue = fields.Datetime(string="Date of Issue", tracking=True)
    mode_of_shipment = fields.Selection([
        ('sea', 'Sea'),
        ('air', 'Air'),
        ('road', 'Road'),
        ('rail', 'Rail'),
        ('courier', 'Courier'),
    ], string="Mode of Shipment", tracking=True)
    bonded_warehouse_expiry = fields.Date(string="Bonded Warehouse Expiry", help="Only available for import, back_to_back, foreign_back_to_back, local_back_to_back, transferable, standby.", tracking=True)


    # Related fields
    # product_line_ids = fields.One2many()
    # extra_cost_ids = fields.One2many()

    # LC - Status, Workflow, Availability & Charges
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('advised', 'Advised'),
        ('active', 'Active'),
        ('amend', 'Amend'),
        ('expired', 'Expired'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', tracking=True)
    reference = fields.Char(string="Reference", help="Internal or bank reference", tracking=True)

    available_by = fields.Selection([
        ('payment', 'By Payment'),
        ('acceptance', 'By Acceptance'),
        ('negotiation', 'By Negotiation'),
        ('deferred_payment', 'By Deferred Payment'),
    ], string="Available By", tracking=True)
    charges_borne_by = fields.Selection([
        ('applicant', 'Applicant'),
        ('beneficiary', 'Beneficiary'),
        ('shared', 'Shared'),
    ], string="Charges Borne By", tracking=True)

    # Revolving LC
    is_revolving = fields.Boolean(string="Revolving LC", tracking=True)
    revolving_period = fields.Integer(string="Revolving Period (days)", tracking=True)
    revolving_limit = fields.Float(string="Revolving Limit", tracking=True)
    parent_lc_id = fields.Many2one('lc.management', string="Parent LC", help="For back-to-back LC linkage", tracking=True)

    # Other Information
    terms_and_conditions = fields.Html(string="Terms and Conditions", help="Terms and conditions of the LC", tracking=True)
    remarks = fields.Text(string="Remarks", tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments", tracking=True)
    attachment_count = fields.Integer(string="Attachments",compute='_compute_attachment_count', tracking=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company, tracking=True
    )

    # Certificates
    noc = fields.Char(string="NOC", tracking=True)
    bin_certificate = fields.Char(string="BIN Certificate", tracking=True)
    tax_clearance_certificate = fields.Char(string="Tax Clearance Certificate", tracking=True)
    etin_certificate = fields.Char(string="ETIN Certificate", tracking=True)

    # Insurance Info
    insurance_policy_no = fields.Char(string="Insurance Policy No", tracking=True)
    insurance_company_id = fields.Many2one('res.partner', string="Insurance Company", tracking=True)

    # Reminders
    reminder_date = fields.Date(string="Reminder Date", help="Date to trigger alert before expiry", tracking=True)

    warning_interval = fields.Selection([
        ('week', '1 Week before'),
        ('month', '1 Month before'),
    ], string="Warning Interval", tracking=True)
    
    currency_rate_line_ids = fields.One2many(
        'lc.currency.rate.line', 'lc_id', string="Currency Rates", readonly=True, tracking=True
    )

    additional_cost_line_ids = fields.One2many('lc.additional.cost.line','lc_id',string="Additional Costs", tracking=True)
    
    # LC Template
    lc_template_id = fields.Many2one(
        'lc.template',
        string="LC Template",
        help="Selecting a template will auto-fill fields and lines like Sales Quotation Template.", tracking=True
    )


    split_method = fields.Selection([
        ('equal', 'Equal'),
        ('by_quantity', 'By Quantity'),
        ('by_current_cost_price', 'By Current Cost'),
        ('by_weight', 'By Weight'),
        ('by_volume', 'By Volume'),
    ], string='Split Method', default='equal', tracking=True)

    # helper for button visibility
    can_split_cost = fields.Boolean(
        compute='_compute_can_split_cost',
        string='Can Split Cost'
    )
    po_cost_line_ids = fields.One2many(
        'lc.po.cost.line',
        'lc_id',
        string="PO Cost Split",
        readonly=True,
    )
    po_cost_line_count = fields.Integer(
        string="PO Cost Lines",
        compute="_compute_po_cost_line_count",
    )

    po_count = fields.Integer(compute='_compute_po_count')

    # It contains POs that are already linked to ANY other LC request.
    blocked_purchase_order_ids = fields.Many2many(
        'purchase.order',
        compute='_compute_blocked_purchase_order_ids',
        string='Blocked Purchase Orders',
        compute_sudo=True,
    )

    is_outdated_po = fields.Boolean(
        string="Outdated PO",
        default=False,
        copy=False,
    )

    def action_submit(self):
        """Move from Draft to Submitted"""
        for record in self:
            if not record.purchase_order_ids:
                raise UserError(_("Please select at least one Purchase Order before submitting."))
            record.status = 'submitted'

    def action_approve(self):
        """Move to Approved and TRIGGER PO LOCK"""
        for record in self:
            record.status = 'approved'

            if record.purchase_order_ids:
                pos_to_lock = record.purchase_order_ids.filtered(lambda p: p.state == 'purchase')
                pos_to_lock.button_done()

                self.message_post(body=Markup("<b>Purchase Orders linked to this LC have been locked automatically.</b>")),


    def action_advise(self):
        self.status = 'advised'

    def action_active(self):
        self.status = 'active'

    def action_amend(self):
        self.status = 'amend'

    def action_close(self):
        self.status = 'closed'

    def action_cancel(self):
        """Cancel the LC Request"""
        self.status = 'cancelled'

    def action_draft(self):
        self.status = 'draft'


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('lc_number'):
                vals['lc_number'] = self.env['ir.sequence'].next_by_code('lc.management') or _('New')

        return super().create(vals_list)


    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        vals['date_of_issue'] = fields.Datetime.now()

        return vals


    @api.onchange('date_of_issue')
    def _check_issue_date_warning(self):
        today = date.today()
        for rec in self:
            if rec.date_of_issue:
                issue_date = rec.date_of_issue.date()
                if issue_date < today:
                    return {
                        'warning': {
                            'title': _('Reminder Date Alert'),
                            'message': _("Issue date is in the past.")
                        }
                    }


    @api.onchange('date_of_issue', 'lc_type')
    def _compute_expiry_date(self):
        for rec in self:
            if not rec.date_of_issue:
                continue
            if rec.lc_type == 'at_sight':
                rec.expiration_date = rec.date_of_issue + timedelta(days=90)
            elif rec.lc_type == 'deferred':
                rec.expiration_date = rec.date_of_issue + timedelta(days=180)
            elif rec.lc_type == 'standby':
                rec.expiration_date = rec.date_of_issue + timedelta(days=365)
            elif rec.lc_type == 'revolving':
                rec.expiration_date = rec.date_of_issue + timedelta(days=365)
            else:
                rec.expiration_date = rec.date_of_issue + timedelta(days=180)


    @api.onchange('warning_interval', 'date_of_issue', 'expiration_date')
    def _compute_reminder_date(self):
        for rec in self:
            if rec.date_of_issue and rec.expiration_date:

                issue_date = fields.Date.to_date(rec.date_of_issue)
                expiry_date = fields.Date.to_date(rec.expiration_date)

                if rec.warning_interval == 'week':
                    rec.reminder_date = expiry_date - timedelta(weeks=1)
                elif rec.warning_interval == 'month':
                    rec.reminder_date = expiry_date - timedelta(days=30)

                if rec.reminder_date:
                    if rec.reminder_date < issue_date or rec.reminder_date > expiry_date:
                        raise ValidationError(_("Reminder date must be between issue and expiry dates."))


    @api.onchange('reminder_date')
    def _onchange_reminder_date_warning(self):
        for rec in self:
            if rec.reminder_date:
                today = date.today()
                if rec.reminder_date <= today:
                    return {
                        'warning': {
                            'title': _('Reminder Date Alert'),
                            'message': _('Reminder Date has already passed or is today. Take necessary action.')
                        }
                    }

    @api.onchange('beneficiary_company_id')
    def _onchange_beneficiary_company_id(self):
        self.beneficiary_id = False

    @api.depends('applicant_id')
    def _compute_applicant_company(self):
        for rec in self:
            user = self.env.user
            if user and user.company_id:
                rec.applicant_company_id = user.company_id.id
            else:
                rec.applicant_company_id = False

    @api.onchange('beneficiary_company_id')
    def _onchange_beneficiary_company_id(self):
        for rec in self:
            # Only reset if the current beneficiary doesn't match the company
            if rec.beneficiary_id and rec.beneficiary_id.parent_id != rec.beneficiary_company_id:
                rec.beneficiary_id = False

            if rec.beneficiary_company_id:
                # Only show child contacts (is_company=False)
                domain = [
                    ('parent_id', '=', rec.beneficiary_company_id.id),
                    ('is_company', '=', False)
                ]
            else:
                domain = [('id', '=', False)]

            return {
                'domain': {
                    'beneficiary_id': domain
                }
            }


    # Button action to compute PO amounts and exchange rates

    def action_compute_po_amount(self):
        for rec in self:
            target_currency = rec.currency_id or rec.env.ref('base.USD')
            rec.currency_rate_line_ids.unlink()
            currency_map = {}
            for po in rec.purchase_order_ids:
                curr = po.currency_id
                if curr not in currency_map:
                    currency_map[curr] = {'amount': 0.0, 'rate': curr.rate}
                currency_map[curr]['amount'] += po.amount_total
            lines = []
            total = 0.0
            for curr, vals in currency_map.items():
                amount_in_target = curr._convert(
                    vals['amount'], target_currency, rec.company_id or self.env.company, fields.Date.today()
                )
                company = rec.company_id or self.env.company

                rate = self.env['res.currency']._get_conversion_rate(
                    from_currency=curr,
                    to_currency=target_currency,
                    company=company,
                    date=fields.Date.today(),
                )

                total += amount_in_target
                lines.append((0, 0, {
                    'currency_id': curr.id,
                    'rate': rate,
                    'amount': vals['amount'],
                    'amount_in_target': amount_in_target,
                }))
            rec.currency_rate_line_ids = lines
            rec.amount = total
            rec.currency_id = target_currency

    def action_update_from_po(self):
        for rec in self:
            if rec.status not in ('draft', 'submitted'):
                continue
            rec.action_compute_po_amount()
            rec.is_outdated_po = False
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Attachments'),
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
        }

    @api.onchange('lc_template_id')
    def _onchange_lc_template_id(self):
        """
        On changing the LC Template, auto-fill fields from the selected template.
        """
        for rec in self:
            template = rec.lc_template_id
            if not template:
                continue

            if template.lc_type:
                rec.lc_type = template.lc_type
            if template.beneficiary_company_id:
                rec.beneficiary_company_id = template.beneficiary_company_id.id
            if template.beneficiary_id:
                rec.beneficiary_id = template.beneficiary_id.id
            if template.issuing_bank_id:
                rec.issuing_bank_id = template.issuing_bank_id.id
            if template.advising_bank_id:
                rec.advising_bank_id = template.advising_bank_id.id
            if template.acc_name:
                rec.acc_name = template.acc_name
            if template.bank_account_id:
                rec.bank_account_id = template.bank_account_id.id
            if template.insurance_policy_no:
                rec.insurance_policy_no = template.insurance_policy_no
            if template.insurance_company_id:
                rec.insurance_company_id = template.insurance_company_id.id
            if template.partial_shipment is not None:
                rec.partial_shipment = template.partial_shipment
            if template.transshipment is not None:
                rec.transshipment = template.transshipment
            if template.required_documents:
                rec.required_documents = template.required_documents
            if template.mode_of_shipment:
                rec.mode_of_shipment = template.mode_of_shipment
            if template.available_by:
                rec.available_by = template.available_by
            if template.charges_borne_by:
                rec.charges_borne_by = template.charges_borne_by
            if template.terms_and_conditions:
                rec.terms_and_conditions = template.terms_and_conditions
            if template.remarks:
                rec.remarks = template.remarks

            # Populate additional cost lines from the template
            line_commands = [(5, 0, 0)]  # clear existing lines of additional cost line
            for line in template.ac_template_line_ids:
                line_vals = {
                    'additional_cost_id': line.additional_cost_id.id,
                    'amount': line.amount,
                    'note': line.note,
                    # add any other fields if necessary
                }
                line_commands.append((0, 0, line_vals))

            rec.additional_cost_line_ids = line_commands

    # ---------------------------------------------------------------
    # Button visibility:
    #  - status must be 'submitted'
    #  - every related PO must have at least one draft vendor bill
    # ---------------------------------------------------------------
    @api.depends(
        'status',
        'purchase_order_ids.invoice_ids.state',
        'purchase_order_ids.invoice_ids.move_type',
    )
    def _compute_can_split_cost(self):
        for rec in self:
            # must be submitted and have at least one PO
            if rec.status != 'submitted' or not rec.purchase_order_ids:
                rec.can_split_cost = False
                continue

            ok = True
            for po in rec.purchase_order_ids:
                bills = po.invoice_ids.filtered(
                    lambda m: m.move_type == 'in_invoice'
                )
                # must have at least one draft bill
                if not bills or all(b.state != 'draft' for b in bills):
                    ok = False
                    break

            rec.can_split_cost = ok


    def action_split_additional_cost(self):
        self.ensure_one()
        StockLandedCost = self.env['stock.landed.cost']

        if not self.additional_cost_line_ids:
            raise UserError(_("Please add additional costs to split."))
        if not self.purchase_order_ids:
            raise UserError(_("Please set purchase orders to split on."))

        old_costs = self.env['stock.landed.cost'].search([
            ('lc_management_id', '=', self.id),
            ('state', '=', 'draft'),
        ])
        old_costs.unlink()


        po_amounts = {po: {} for po in self.purchase_order_ids}

        # Compute how much of each LC additional cost line goes to each PO
        for line in self.additional_cost_line_ids:
            if not line.amount:
                continue

            amounts_by_po = self._split_line_amount_by_po(line)

            for po, amount in amounts_by_po.items():
                if not amount:
                    continue
                po_amounts[po].setdefault(line, 0.0)
                po_amounts[po][line] += amount

        self.po_cost_line_ids.unlink()

        PoCostLine = self.env['lc.po.cost.line']
        for po, line_map in po_amounts.items():
            for ac_line, amount in line_map.items():
                if not amount:
                    continue
                PoCostLine.create({
                    'lc_id': self.id,
                    'purchase_id': po.id,
                    'additional_cost_line_id': ac_line.id,
                    'amount': amount,
                })

        created_costs = self.env['stock.landed.cost']
        for po, amounts in po_amounts.items():
            if not amounts:
                continue

            pickings = po.picking_ids.filtered(lambda p: p.state == 'done')
            if not pickings:
                continue

            bill = po.invoice_ids.filtered(
                lambda inv: inv.move_type == 'in_invoice' and inv.state in ('draft', 'posted')
            )[:1]

            cost_lines_vals = []
            for ac_line, amount in amounts.items():
                additional_cost = ac_line.additional_cost_id
                product = additional_cost.product_id

                expense_account = (
                        product.property_account_expense_id
                        or product.categ_id.property_account_expense_categ_id
                )
                if not expense_account:
                    raise UserError(_(
                        "Please configure an expense account for product '%s' or its category."
                    ) % product.display_name)

                cost_lines_vals.append((0, 0, {
                    'name': additional_cost.name or product.display_name,
                    'product_id': product.id,
                    'split_method': self.split_method or 'equal',
                    'price_unit': amount,
                    'account_id': expense_account.id,
                }))

            vals = {
                'lc_management_id': self.id,
                'vendor_bill_id': bill.id if bill else False,
                'picking_ids': [(6, 0, pickings.ids)],
                'cost_lines': cost_lines_vals,
            }
            cost = StockLandedCost.create(vals)
            created_costs |= cost




    def _split_line_amount_by_po(self, line):
        """
        Split one LC additional cost line amount over purchase_order_ids.

        Uses LC's split_method:
          - equal
          - by_quantity
          - by_weight
          - by_volume
          - by_current_cost_price
        """
        self.ensure_one()
        po_list = list(self.purchase_order_ids)
        if not po_list:
            return {}

        total_line = len(po_list) or 1

        qty_by_po = {}
        weight_by_po = {}
        volume_by_po = {}
        cost_by_po = {}


        for po in po_list:
            qty_by_po[po.id] = sum(po.order_line.mapped('product_qty'))

            w = v = c = 0.0
            for pol in po.order_line:
                qty = pol.product_qty
                prod = pol.product_id
                w += (prod.weight or 0.0) * qty
                v += (prod.volume or 0.0) * qty
                c += pol.price_subtotal
            weight_by_po[po.id] = w
            volume_by_po[po.id] = v
            cost_by_po[po.id] = c

        total_qty = sum(qty_by_po.values())
        total_weight = sum(weight_by_po.values())
        total_volume = sum(volume_by_po.values())
        total_cost = sum(cost_by_po.values())

        total_amount = line.amount or 0.0
        if not total_amount:
            return {po: 0.0 for po in po_list}

        # use LC company currency for rounding
        currency = self.company_id.currency_id or self.env.company.currency_id
        rounding = currency.rounding or 0.01

        result = {}
        value_split = 0.0

        method = self.split_method or 'equal'

        for idx, po in enumerate(po_list):
            is_last = (idx == len(po_list) - 1)
            value = 0.0

            if method == 'by_quantity' and total_qty:
                per_unit = total_amount / total_qty
                value = qty_by_po.get(po.id, 0.0) * per_unit

            elif method == 'by_weight' and total_weight:
                per_unit = total_amount / total_weight
                value = weight_by_po.get(po.id, 0.0) * per_unit

            elif method == 'by_volume' and total_volume:
                per_unit = total_amount / total_volume
                value = volume_by_po.get(po.id, 0.0) * per_unit

            elif method == 'by_current_cost_price' and total_cost:
                per_unit = total_amount / total_cost
                value = cost_by_po.get(po.id, 0.0) * per_unit

            elif method == 'equal':
                value = total_amount / total_line

            else:
                value = total_amount / total_line

            if rounding:
                if is_last:
                    value = total_amount - value_split
                    value = tools.float_round(
                        value,
                        precision_rounding=rounding,
                        rounding_method='HALF-UP',
                    )
                else:
                    value = tools.float_round(
                        value,
                        precision_rounding=rounding,
                        rounding_method='HALF-UP',
                    )
                    value_split += value

            result[po] = value

        return result

    def _compute_po_cost_line_count(self):
        for rec in self:
            rec.po_cost_line_count = len(rec.po_cost_line_ids)

    def action_view_po_cost_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "lc_management.action_lc_po_cost_line"
        )

        action["domain"] = [("lc_id", "=", self.id)]
        action["context"] = dict(self.env.context, default_lc_id=self.id)
        return action

    @api.depends('purchase_order_ids')
    def _compute_po_count(self):
        for record in self:
            record.po_count = len(record.purchase_order_ids)

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'context': {'create': False},
            'target': 'current',
        }


    @api.depends('purchase_order_ids')
    def _compute_blocked_purchase_order_ids(self):
        """All POs linked to any other LC (so we can exclude them via domain)."""
        # Read relation table directly
        self.env.cr.execute(
            "SELECT lc_id, purchase_id FROM lc_management_purchase_order_rel"
        )
        rows = self.env.cr.fetchall()

        used_all = {purchase_id for (_, purchase_id) in rows}

        # For each record: block every used PO except the ones already on this record
        for rec in self:
            keep = set(rec.purchase_order_ids.ids)
            blocked = list(used_all - keep)
            rec.blocked_purchase_order_ids = [(6, 0, blocked)]


    @api.constrains('purchase_order_ids')
    def _check_duplicate_purchase_orders(self):
        """Server-side guarantee: a PO cannot be linked to multiple LC requests."""
        for rec in self:
            for po in rec.purchase_order_ids:
                other = self.search([
                    ('id', '!=', rec.id),
                    ('purchase_order_ids', 'in', po.id),
                ], limit=1)
                if other:
                    raise ValidationError(_(
                        "Purchase Order '%s' is already linked to LC '%s'."
                    ) % (po.name, other.lc_number))

    # Override write to lock linked POs when LC is approved
    def write(self, vals):
        res = super(LcManagement, self).write(vals)
        if vals.get('status') == 'approved':
            for record in self:
                if record.purchase_order_ids:
                    record.purchase_order_ids.filtered(lambda p: p.state == 'purchase').button_done()
                    for po in record.purchase_order_ids:
                        po.sudo().message_post(
                            body=Markup("<b>%s</b><br/>%s") % (
                                _("Purchase Order locked"),
                                _("Locked automatically because LC %s was approved.") % (record.display_name,),
                            )
                        )
        return res





