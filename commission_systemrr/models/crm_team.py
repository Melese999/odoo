from odoo import models, fields


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    commission_rule_ids = fields.Many2many(
        'commission_system.rules',
        string="Commission Rules",
        help="Rules applicable to this sales team"
    )