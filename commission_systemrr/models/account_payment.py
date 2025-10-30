from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    crv_number = fields.Char(string="CRV Number")
