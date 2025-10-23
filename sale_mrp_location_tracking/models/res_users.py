from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    production_location_id = fields.Many2one(
        'stock.location', string='Production Location',
        help='Plant/production location assigned to this user for filtering MOs.')
