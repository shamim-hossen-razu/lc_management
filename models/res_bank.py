from odoo import api, fields, models

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