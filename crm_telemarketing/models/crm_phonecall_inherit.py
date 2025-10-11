from odoo import models, fields

class CrmPhonecall(models.Model):
    _inherit = 'crm.phonecall'

    # FR-K-09: Add Customer Satisfaction Survey fields
    service_rating = fields.Selection(
        [('1', 'Poor'), ('2', 'Fair'), ('3', 'Good'), ('4', 'Very Good'), ('5', 'Excellent')],
        string="Service Satisfaction"
    )
    product_rating = fields.Selection(
        [('1', 'Poor'), ('2', 'Fair'), ('3', 'Good'), ('4', 'Very Good'), ('5', 'Excellent')],
        string="Product Satisfaction"
    )
    name_confirmed = fields.Boolean(string="Name Confirmed")
    address_confirmed = fields.Boolean(string="Address Confirmed")
    phone_confirmed = fields.Boolean(string="Phone Confirmed")
    email_confirmed = fields.Boolean(string="Email Confirmed")
    notes = fields.Text(string="Additional Notes")
