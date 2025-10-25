from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_commissionable = fields.Boolean(
        string="Is Commissionable",
        default=True,
        help="Indicates whether this product qualifies for commissions."
    )