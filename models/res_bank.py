from odoo import api, fields, models, _

class ResBank(models.Model):
    _inherit = 'res.bank'

    bank_role_capabilities = fields.Many2many('lc.bank.role', 'res_bank_lc_role_rek', 'bank_id', 'role_id',
                                              string="LC Role Capabilities",
                                              help="Select all LC roles this bank can act in (e.g. advising, confirming, reimbursing, negotiating, issuing, nominated)."
                                              )

    iban = fields.Char(string='IBAN', help="IBAN used on settlement instructions and LC messages.")
    branch_code = fields.Char(string='Branch Code', help="Internal or market branch code where LC operations are processed.")
    routing_number = fields.Char(string='Routing Number')

    iban_required = fields.Boolean(string='IBAN Required', help="Enforce IBAN presence when generating instructions to this bank.")
    swift_required = fields.Boolean(string='Swift Required', help="Enforce BIC presence on all messages to this bank.")


class LCBankRole(models.Model):
    _name = 'lc.bank.role'
    _description = 'LC Bank Role'

    name = fields.Char(string='Bank Role')


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    is_default_lc_account = fields.Boolean(string="Default LC Account", help="This account will be used as the default when creating a new LC.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records.filtered('is_default_lc_account'):
            rec._ensure_single_default()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'is_default_lc_account' in vals and vals['is_default_lc_account']:
            for rec in self.filtered(lambda r: r.is_default_lc_account):
                rec._ensure_single_default()
        return res

    def _ensure_single_default(self):
        for rec in self:
            self.env['res.partner.bank'].search([
                ('partner_id', '=', rec.partner_id.id), ('bank_id', '=', rec.bank_id.id), ('id', '!=', rec.id), ('is_default_lc_account', '=', True)
            ]).write({'is_default_lc_account': False})


    @api.onchange('is_default_lc_account')
    def _onchange_is_default_lc_account(self):
        for rec in self:
            if rec.is_default_lc_account:
                existing_default = self.env['res.partner.bank'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('bank_id', '=', rec.bank_id.id),
                    ('is_default_lc_account', '=', True),
                    ('id', '!=', rec.id),
                ], limit=1)

                if existing_default:
                    return {
                        'warning': {
                            'title': _('Another Default Already Exists'),
                            'message': _(
                                "The partner '%s' already has a default LC bank account:\n"
                                "- %s (%s)\n\n"
                                "Setting this account as default will replace the existing one."
                            ) % (
                                           rec.partner_id.display_name,
                                           existing_default.acc_number or _('N/A'),
                                           existing_default.bank_id.name or _('Unknown Bank')
                                       )
                        }
                    }