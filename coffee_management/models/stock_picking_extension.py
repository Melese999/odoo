from odoo import fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    coffee_contract_id = fields.Many2one('coffee.contract', string='Source Coffee Contract', copy=False, index=True, readonly=True)