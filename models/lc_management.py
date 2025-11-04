from odoo import models, fields, api, _
from datetime import date


class LcManagement(models.Model):
    _name = 'lc.management'
    _description = 'Letter of Credit Management'
    _rec_name = 'lc_number'

    # LC related basic information and its types
    lc_number = fields.Char(string="LC Number", readonly=True, copy=False)

    applicant_id = fields.Many2one('res.partner', string="Applicant", help="Buyer applying for the LC")
    beneficiary_id = fields.Many2one('res.partner', string="Beneficiary", help="Seller or exporter")

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
    acc_name = fields.Char(string="Account Name")
    account_no = fields.Integer(string="Account Number")

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
    bonded_warehouse_expiry = fields.Date(string="Bonded Warehouse Expiry")

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


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('lc_number'):
                vals['lc_number'] = self.env['ir.sequence'].next_by_code('lc.management') or _('New')

        return super().create(vals_list)