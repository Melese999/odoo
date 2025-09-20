from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # You can add specific fields here if needed, e.g.,
    coffee_supplier_code = fields.Char(string='Coffee Supplier Code')
    coffee_buyer_code = fields.Char(string='Coffee Buyer Code')
    #pass
