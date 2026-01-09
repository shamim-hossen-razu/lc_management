from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LcTemplate(models.Model):
    _name = 'lc.template'
    _description = 'LC Template'
    _order = 'priority desc, create_date desc, id desc'

    name = fields.Char(string="Template Name", required=True)
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Urgent')], 'Priority', default='0', index=True)

    # Fields that want to be pre-defined in the template
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

    beneficiary_company_id = fields.Many2one('res.partner', string="Beneficiary Company",
                                             domain=[('is_company', '=', True)], help="Company supplying the goods")
    beneficiary_id = fields.Many2one('res.partner', string="Beneficiary", domain=[],
                                     help="Individual contact under the selected company (Seller/Exporter)")

    issuing_bank_id = fields.Many2one('res.bank', string="Issuing Bank", help="Bank issuing the LC for the buyer", copy=False)
    advising_bank_id = fields.Many2one('res.bank', string="Advising Bank", help="Bank advising the LC to the seller", copy=False)

    acc_name = fields.Char(string="Account Name", copy=False)
    bank_account_id = fields.Many2one('res.partner.bank', string="Account No", help="Bank account number", copy=False)

    # Insurance Info
    insurance_policy_no = fields.Char(string="Insurance Policy No")
    insurance_company_id = fields.Many2one('res.partner', string="Insurance Company")

    ac_template_line_ids = fields.One2many(
        'lc.template.ac.line',
        'template_id',
        string="Additional Costs",
    )

    # shipment information
    partial_shipment = fields.Boolean(string="Partial Shipment Allowed")
    transshipment = fields.Boolean(string="Transshipment Allowed")
    required_documents = fields.Html(string="Required Documents", help="Invoice, Packing List, B/L, Insurance, etc.")
    mode_of_shipment = fields.Selection([
        ('sea', 'Sea'),
        ('air', 'Air'),
        ('road', 'Road'),
        ('rail', 'Rail'),
        ('courier', 'Courier'),
    ], string="Mode of Shipment")

    # Terms of Delivery
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

    # Certificates
    noc = fields.Char(string="NOC")
    bin_certificate = fields.Char(string="BIN Certificate")
    tax_clearance_certificate = fields.Char(string="Tax Clearance Certificate")
    etin_certificate = fields.Char(string="ETIN Certificate")

    # Other Information
    terms_and_conditions = fields.Html(string="Terms and Conditions", help="Terms and conditions of the LC")
    remarks = fields.Text(string="Remarks")

    @api.constrains('bank_account_id')
    def _check_unique_bank_account(self):
        for record in self:
            if record.bank_account_id:
                duplicate = self.search([
                    ('bank_account_id', '=', record.bank_account_id.id),
                    ('id', '!=', record.id)
                ], limit=1)

                if duplicate:
                    raise ValidationError(_(
                        "This bank account (%s) is already used in another LC Template: %s. "
                        "Please select a different bank account."
                    ) % (record.bank_account_id.acc_number, duplicate.name))

    def copy_data(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.setdefault('name', _("%s (copy)") % (self.name or _("New")))
        return super().copy_data(default)

    @api.onchange('beneficiary_company_id')
    def _onchange_beneficiary_company_id(self):
        self.beneficiary_id = False
