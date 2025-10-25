from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    telemarketing_prefix = fields.Char(
        string="Telemarketing Confirmation Prefix",
        default='CONF',
        help="Prefix used for Telemarketing Confirmation sequence numbers."
    )

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'telemarketing.confirmation.prefix',
            self.telemarketing_prefix
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update({
            'telemarketing_prefix': self.env['ir.config_parameter'].sudo().get_param(
                'telemarketing.confirmation.prefix', default='CONF'
            ),
        })
        return res
