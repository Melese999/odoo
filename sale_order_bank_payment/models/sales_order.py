from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrderBankPayment(models.Model):
    _name = 'sale.order.bank.payment'
    _description = 'Sales Order Bank Payment'

    sale_order_id = fields.Many2one(
        'sale.order', string='Sales Order', ondelete='cascade'
    )
    bank_account_id = fields.Many2one(
        'res.bank', string='Bank', required=True
    )
    tt_number = fields.Char(
        string='TT Number', required=True
    )
    amount = fields.Float(
        string='Amount', required=True
    )

    _sql_constraints = [
        ('unique_tt_number', 'unique(tt_number)', 'The TT number must be unique!')
    ]

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("The amount must be greater than zero.")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    bank_account_payment_ids = fields.One2many(
        'sale.order.bank.payment', 'sale_order_id', string='Bank Payments'
    )

    advance_payment = fields.Float(
        string='Advance Payment',
        compute='_compute_advance_payment',
        store=True,
        readonly=True
    )

    @api.depends('bank_account_payment_ids.amount')
    def _compute_advance_payment(self):
        for order in self:
            order.advance_payment = sum(order.bank_account_payment_ids.mapped('amount'))
