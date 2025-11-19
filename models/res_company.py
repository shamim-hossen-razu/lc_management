from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    is_importer = fields.Boolean(string="Is Importer")
    is_exporter = fields.Boolean(string="Is Exporter")

    trade_license_no = fields.Char(string="Trade License No.")
    trade_license_expiry = fields.Date(string="Trade License Expiry")
    trade_license_file = fields.Binary(string="Trade License File")
    trade_license_filename = fields.Char(string="Trade License File PDF Filename")

    etin_no = fields.Char(string="eTIN No.")
    etin_file = fields.Binary(string="eTIN File")
    etin_filename = fields.Char(string="eTIN File PDF Filename")

    bin_no = fields.Char(string="BIN No.")
    bin_file = fields.Binary(string="BIN File")
    bin_filename = fields.Char(string="BIN File PDF Filename")

    vat_circle = fields.Char(string="VAT Circle")

    irc_no = fields.Char(string="IRC No.")
    irc_expiry = fields.Date(string="IRC Expiry")
    irc_file = fields.Binary(string="IRC File")
    irc_filename = fields.Char(string="IRC File PDF Filename")

    erc_no = fields.Char(string="ERC No.")
    erc_expiry = fields.Date(string="ERC Expiry")

    rjsc_reg_no = fields.Char(string="RJSC Registration No.")
    rjsc_file = fields.Binary(string="RJSC Registration File")
    rjsc_filename = fields.Char(string="RJSC Registration PDF Filename")

    association_membership_id = fields.Many2one('association.membership', string="Association Membership")

    association_membership_name = fields.Char(string="Association Name")
    am_governing_body = fields.Char(string="Governing Body")
    am_membership_code = fields.Char(string="Membership Code")
    am_issue_date = fields.Date(string="Issue Date")
    am_expiry_date = fields.Date(string="Expiry Date")
    am_certificate_file = fields.Binary(string="Membership Certificate File")
    am_certificate_filename = fields.Char(string="Membership Certificate PDF Filename")
    am_note = fields.Text(string="Notes")
    am_state = fields.Selection([
        ('valid', 'Valid'),
        ('expired', 'Expired')
    ], string="State", compute="_compute_state", store=True)

    bonded_warehouse_license_no = fields.Char(string="Bonded Warehouse License No.")
    bonded_warehouse_expiry = fields.Date(string="Bonded Warehouse Expiry")

    custom_reg_no = fields.Char(string="Custom Registration No.")

    tax_clearance_no = fields.Char(string="Tax Clearance No.")
    tax_clearance_expiry = fields.Date(string="Tax Clearance Expiry")
    tax_clearance_file = fields.Binary(string="Tax Clearance File")
    tax_clearance_filename = fields.Char(string="Tax Clearance PDF Filename")

    partnership_deed_file = fields.Binary(string="Partnership Deed File")
    partnership_deed_filename = fields.Char(string="Partnership Deed PDF Filename")
    moa_file = fields.Binary(string="MOA File")
    moa_filename = fields.Char(string="MOA File PDF Filename")

    notes = fields.Text(string="Notes")


    def _get_document_fields(self):
        return [
            'trade_license_file',
            'rjsc_file',
            'etin_file',
            'bin_file',
            'irc_file',
            'tax_clearance_file',
            'partnership_deed_file',
            'moa_file',
            'am_certificate_file',
        ]


    def _get_or_create_company_tag(self):
        self.ensure_one()

        Tag = self.env['documents.tag']
        tag = Tag.search([('name', '=', self.name)], limit=1)

        if not tag:
            tag = Tag.create({'name': self.name})

        return tag


    def _sync_compliance_documents(self, vals):
        Attachment = self.env['ir.attachment']
        Document = self.env['documents.document']

        for record in self:
            tag = record._get_or_create_company_tag()

            for field in record._get_document_fields():
                if field in vals and vals.get(field):
                    file_data = vals.get(field)
                    filename = vals.get(f"{field}_filename", f"{field}.pdf")

                    # -----------------------------------------------------------
                    # Step 1: Find and delete any old attachment/document records
                    # -----------------------------------------------------------

                    old_attachment = Attachment.search([
                        ('res_model', '=', 'res.company'),
                        ('res_id', '=', record.id),
                        ('res_field', '=', field),
                    ])

                    if old_attachment:
                        old_doc = Document.search([
                            ('attachment_id', '=', old_attachment.id),
                        ], limit=1)

                        if old_doc:
                            old_doc.unlink()

                        old_attachment.unlink()

                    # -----------------------------------------------------------
                    # Step 2: Create a fresh ir.attachment for the new upload
                    # -----------------------------------------------------------

                    new_attachment = Attachment.create({
                        'name': filename,
                        'datas': file_data,
                        'res_model': 'res.company',
                        'res_id': record.id,
                        'res_field': field,
                        'type': 'binary',
                    })

                    # -----------------------------------------------------------
                    # Step 3: Create a linked documents.document record
                    # -----------------------------------------------------------

                    Document.create({
                        'name': filename,
                        'attachment_id': new_attachment.id,
                        'owner_id': self.env.user.id,
                        'res_model': 'res.company',
                        'res_id': record.id,
                        'tag_ids': [(6, 0, [tag.id])],
                    })


    def _validate_compliance_documents(self):
        """Validate required compliance documents only when saving"""
        today = date.today()

        for company in self:
            # --- TRADE LICENSE ---
            if not company.trade_license_no or not company.trade_license_file:
                raise ValidationError(_(
                    "Trade License is mandatory.\n"
                    "Please provide Trade License Number and upload the file."
                ))

            if company.trade_license_expiry and company.trade_license_expiry < today:
                raise ValidationError(_(
                    "Trade License is expired (%s). Please update the expiry date."
                ) % (company.trade_license_expiry))

            # --- BIN ---
            if not company.bin_no or not company.bin_file:
                raise ValidationError(_(
                    "Business Identification Number (BIN) is mandatory.\n"
                    "Please enter BIN Number and upload the BIN document."
                ))

            # --- eTIN ---
            if not company.etin_no or not company.etin_file:
                raise ValidationError(_(
                    "Electronic Tax Identification Number (eTIN) is mandatory.\n"
                    "Please provide eTIN Number and upload the eTIN file."
                ))

            # --- IRC (for Importers) ---
            if company.is_importer:
                if not company.irc_no or not company.irc_file:
                    raise ValidationError(_(
                        "Import Registration Certificate (IRC) is required for importers.\n"
                        "Please provide IRC Number and upload the IRC document."
                    ))

                if company.irc_expiry and company.irc_expiry < today:
                    raise ValidationError(_(
                        "IRC Certificate is expired (%s)."
                    ) % (company.irc_expiry))


    def write(self, vals):
        res = super().write(vals)
        if self.exists():
            self._validate_compliance_documents()
        self._sync_compliance_documents(vals)
        return res


    @api.model_create_multi
    def create(self, vals):
        company = super().create(vals)
        self._sync_compliance_documents(vals)
        return company


    document_count = fields.Integer(string="Documents", compute='_compute_document_count')

    def _compute_document_count(self):
        Document = self.env['documents.document']
        for company in self:
            count = Document.search_count([('res_model', '=', 'res.company'), ('res_id', '=', company.id)])
            company.document_count = count


    def action_view_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Company Documents',
            'res_model': 'documents.document',
            'view_mode': 'list,form',
            'domain': [
                ('res_model', '=', 'res.company'),
                ('res_id', '=', self.id),
            ],
            'context': {
                'default_res_model': 'res.company',
                'default_res_id': self.id,
            },
        }


    @api.depends('am_expiry_date')
    def _compute_state(self):
        today = date.today()
        for record in self:
            if record.am_expiry_date and record.am_expiry_date < today:
                record.am_state = 'expired'
            else:
                record.am_state = 'valid'