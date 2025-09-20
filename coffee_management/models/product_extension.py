from odoo import fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    weight_per_bag = fields.Float(string='Weight per Bag (KG)', default=1.0)
    esex_grade = fields.Selection([('UG', 'UG'), ('G5', 'G5'), ('G4', 'G4'), ('G3', 'G3'), ('G2', 'G2'), ('G1', 'G1')], string='ESEX Grade')
    amg_grade = fields.Selection([('UG', 'UG'), ('G5', 'G5'), ('G4', 'G4'), ('G3', 'G3'), ('G2', 'G2'), ('G1', 'G1')], string='AMG Grade')
    is_coffee_product = fields.Boolean(string='Is Coffee Product')