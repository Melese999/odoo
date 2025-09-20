from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    coffee_type_id = fields.Many2one('product.attribute.value', string='Coffee Type', domain="[('attribute_id.name', '=', 'Coffee Type')]")
    coffee_origin_id = fields.Many2one('product.attribute.value', string='Coffee Origin', domain="[('attribute_id.name', '=', 'Coffee Origin')]")
    coffee_grade_id = fields.Many2one('product.attribute.value', string='Coffee Grade', domain="[('attribute_id.name', '=', 'Coffee Grade')]")
    is_coffee_product = fields.Boolean(string="Is a Coffee Product", default=False)