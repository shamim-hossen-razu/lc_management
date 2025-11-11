from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import ValidationError
from lxml import etree

class LcManagement(models.Model):
    _name = 'lc.management'
    _description = 'Letter of Credit Management'
    _rec_name = 'lc_number'

    # LC related basic information and its types
    lc_number = fields.Char(string="LC Number", readonly=True, copy=False)

    applicant_id = fields.Many2one(
        'res.partner',
        string="Applicant",
        default=lambda self: self.env.user.partner_id,
        readonly=True,
        help="Buyer applying for the LC")
    applicant_company_id = fields.Many2one(
        'res.company',
        string="Applicant Company",
        compute="_compute_applicant_company",
        store=True, readonly=True,
        help="Parent company of the logged-in user")

    beneficiary_company_id = fields.Many2one(
        'res.partner',
        string="Beneficiary Company",
        domain=[('is_company', '=', True)],
        help="Company supplying the goods")
    beneficiary_id = fields.Many2one(
        'res.partner',
        string="Beneficiary",
        domain=[],
        help="Individual contact under the selected company (Seller/Exporter)")

    issuing_bank_id = fields.Many2one('res.bank', string="Issuing Bank", help="Bank issuing the LC for the buyer")
    advising_bank_id = fields.Many2one('res.bank', string="Advising Bank", help="Bank advising the LC to the seller")

    amount = fields.Float(string="Amount", help="Total amount guaranteed by the LC")
    expiration_date = fields.Date(string="Expiration Date", help="Expiration date of the LC")
    terms_and_conditions = fields.Html(string="Terms and Conditions", help="Terms and conditions of the LC")

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
    ], string="LC Type", required=True)

    # Currency and finance information
    currency_id = fields.Many2one('res.currency', string="Currency", help="Currency of the LC amount")
    currency_rate = fields.Float(string="Currency Exchange Rate")
    margin_percentage = fields.Float(string="Margin Percentage", help="Margin required by the issuing bank")

    # Selected bank account under that bank (filtered by applicant company)
    bank_account_id = fields.Many2one(
        'res.partner.bank',
        string="Bank Account Name",
        domain=[('bank_id', '=', issuing_bank_id), ('company_id', '=', applicant_company_id)],
        help="Bank account of applicant company at selected bank")
    acc_holder_name = fields.Char(string="Account Holder Name", compute="_compute_bank_account_details", store=True)
    account_no = fields.Char(string="Account Number", compute="_compute_bank_account_details", store=True)

    # shipment information
    partial_shipment = fields.Boolean(string="Partial Shipment Allowed")
    transshipment = fields.Boolean(string="Transshipment Allowed")
    required_documents = fields.Html(string="Required Documents", help="Invoice, Packing List, B/L, Insurance, etc.")
    date_of_issue = fields.Datetime(string="Date of Issue")
    mode_of_shipment = fields.Selection([
        ('sea', 'Sea'),
        ('air', 'Air'),
        ('road', 'Road'),
        ('rail', 'Rail'),
        ('courier', 'Courier'),
    ], string="Mode of Shipment")
    bonded_warehouse_expiry = fields.Date(string="Bonded Warehouse Expiry", help="Only available for import, back_to_back, foreign_back_to_back, local_back_to_back, transferable, standby.")

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
    ], string="Status", default='draft')
    reference = fields.Char(string="Reference", help="Internal or bank reference")

    available_by = fields.Selection([
        ('payment', 'By Payment'),
        ('acceptance', 'By Acceptance'),
        ('negotiation', 'By Negotiation'),
        ('deferred_payment', 'By Deferred Payment'),
    ], string="Available By")
    charges_borne_by = fields.Selection([
        ('applicant', 'Applicant'),
        ('beneficiary', 'Beneficiary'),
        ('shared', 'Shared'),
    ], string="Charges Borne By")

    # Revolving LC
    is_revolving = fields.Boolean(string="Revolving LC")
    revolving_period = fields.Integer(string="Revolving Period (days)")
    revolving_limit = fields.Float(string="Revolving Limit")
    parent_lc_id = fields.Many2one('lc.management', string="Parent LC", help="For back-to-back LC linkage")

    # Other Information
    remarks = fields.Text(string="Remarks")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")

    # Certificates
    noc = fields.Char(string="NOC")
    bin_certificate = fields.Char(string="BIN Certificate")
    tax_clearance_certificate = fields.Char(string="Tax Clearance Certificate")
    etin_certificate = fields.Char(string="ETIN Certificate")

    # Insurance Info
    insurance_policy_no = fields.Char(string="Insurance Policy No")
    insurance_company_id = fields.Many2one('res.partner', string="Insurance Company")

    # Reminders
    reminder_date = fields.Date(string="Reminder Date", help="Date to trigger alert before expiry")

    warning_interval = fields.Selection([
        ('week', '1 Week before'),
        ('month', '1 Month before'),
    ], string="Warning Interval")


    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if 'issuing_bank_id' in res:
            partner = self.env.user.partner_id
            if partner:
                accounts = self.env['res.partner.bank'].search([('partner_id', '=', partner.id)])
                bank_ids = accounts.mapped('bank_id').ids
                res['issuing_bank_id']['domain'] = [('id', 'in', bank_ids)]
        return res


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('lc_number'):
                vals['lc_number'] = self.env['ir.sequence'].next_by_code('lc.management') or _('New')

            if not vals.get('issuing_bank_id') or not vals.get('bank_account_id'):
                partner = self.env.user.partner_id
                accounts = self.env['res.partner.bank'].search([('partner_id', '=', partner.id)])

                if accounts:
                    default = accounts.filtered('is_default_lc_account')

                    # CASE 1: Only one account
                    if len(accounts) == 1:
                        selected_account = accounts[0]

                    # CASE 2: Multiple with default
                    elif default:
                        selected_account = default[0]

                    # CASE 3: Multiple without default
                    else:
                        selected_account = accounts[0]

                    vals.setdefault('issuing_bank_id', selected_account.bank_id.id)
                    vals.setdefault('bank_account_id', selected_account.id)

        return super().create(vals_list)


    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)

        user_partner = self.env.user.partner_id

        if 'issuing_bank_id' in fields_list:
            accounts = self.env['res.partner.bank'].search([('partner_id', '=', user_partner.id)])
            bank_ids = accounts.mapped('bank_id').ids

            # Inject domain context
            self = self.with_context({
                'default_issuing_bank_id_domain': [('id', 'in', bank_ids)]
            })

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

    @api.depends('applicant_id')
    def _compute_applicant_company(self):
        for rec in self:
            user = self.env.user
            if user and user.company_id:
                rec.applicant_company_id = user.company_id.id  # assign ID
            else:
                rec.applicant_company_id = False

    @api.onchange('beneficiary_company_id')
    def _onchange_beneficiary_company_id(self):
        for rec in self:
            rec.beneficiary_id = False  # Clear selection each time

            if rec.beneficiary_company_id:
                # Only show child contacts (is_company=False)
                domain = [
                    ('parent_id', '=', rec.beneficiary_company_id.id),
                    ('is_company', '=', False)
                ]
            else:
                domain = [('id', '=', False)]  # Show nothing

            return {
                'domain': {
                    'beneficiary_id': domain
                }
            }


    @api.depends('bank_account_id')
    def _compute_bank_account_details(self):
        for rec in self:
            if rec.bank_account_id:
                rec.acc_holder_name = rec.bank_account_id.acc_holder_name
                rec.account_no = rec.bank_account_id.acc_number
            else:
                rec.acc_holder_name = False
                rec.account_no = False


    @api.onchange('issuing_bank_id')
    def _onchange_issuing_bank_id(self):
        for rec in self:
            rec.bank_account_id = False

            if not rec.issuing_bank_id or not rec.applicant_company_id:
                return

            accounts = self.env['res.partner.bank'].search([
                ('bank_id', '=', rec.issuing_bank_id.id), ('partner_id', '=', rec.applicant_id.id)
            ])

            if not accounts:
                rec.issuing_bank_id = False

                return {
                    'warning': {
                        'title': _('Missing Bank Account'),
                        'message': _(
                            'The selected bank has no account for the applicant\'s company.\n'
                            'Please create one before proceeding.'
                        )
                    }
                }

            if len(accounts) == 1:
                rec.bank_account_id = accounts[0]
                return

            default = accounts.filtered('is_default_lc_account')
            if default:
                rec.bank_account_id = default[0]
            else:
                rec.bank_account_id = accounts[0]