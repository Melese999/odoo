# models/account_move_extension.py

# -*- coding: utf-8 -*-
from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    coffee_contract_id = fields.Many2one(
        'coffee.contract',
        string='Source Coffee Contract',
        readonly=True,
        copy=False
    )
