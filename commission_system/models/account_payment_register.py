# models/account_payment_register.py

from odoo import models, fields

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    crv_number = fields.Char(string="CRV Number", help="Enter the Cash Receipt Voucher number from the register.")
    def _create_payments(self):
        payments = super()._create_payments()
        # Write CRV number to created payments
        if self.crv_number:
            payments.write({'crv_number': self.crv_number})
        return payments
