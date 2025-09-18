from email.policy import default

from odoo import api ,models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    latitude = fields.Float("Latitude", digits=(16, 6))
    longitude = fields.Float("Longitude", digits=(16, 6))
    company_ids = fields.Many2many(
        "res.company", 
        string="Companies", 
        required=True,
        help="Link market intelligence to your companies."
    )