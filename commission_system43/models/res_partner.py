from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_agent = fields.Boolean(string="Is Agent", default=False)
    bank_account_id = fields.Many2one(
        'res.partner.bank',
        string="Primary Bank Account",
        domain="[('partner_id', '=', id)]"
    )

    # Computed fields for bank details
    bank_name = fields.Char(
        string="Bank Name",
        compute="_compute_bank_details",
        store=True
    )
    iban = fields.Char(
        string="IBAN",
        compute="_compute_bank_details",
        store=True
    )

    @api.depends('bank_account_id')
    def _compute_bank_details(self):
        for partner in self:
            partner.bank_name = partner.bank_account_id.bank_id.name if partner.bank_account_id else False
            partner.iban = partner.bank_account_id.acc_number if partner.bank_account_id else False

    # Automatically set account holder name when saving bank account
    @api.model
    def create(self, vals):
        if vals.get('is_agent') and vals.get('bank_account_id'):
            bank_account = self.env['res.partner.bank'].browse(vals['bank_account_id'])
            bank_account.write({'acc_holder_name': vals.get('name')})
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        if 'bank_account_id' in vals or 'name' in vals:
            for agent in self.filtered('is_agent'):
                if agent.bank_account_id:
                    agent.bank_account_id.acc_holder_name = agent.name
        return res

    def _compute_bank_count(self):
        for partner in self:
            partner.bank_count = len(partner.bank_ids)

    def action_view_bank_accounts(self):
        self.ensure_one()
        return {
            'name': _('Bank Accounts'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.bank',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }


