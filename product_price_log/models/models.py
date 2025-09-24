# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class ProductPriceLog(models.Model):
    _name = "product.price.log"
    _description = "Product Price Log"

    product_id = fields.Many2one('product.product', string="Product", required=True)
    old_price = fields.Float(string="Old Price")
    new_price = fields.Float(string="New Price")
    changed_date = fields.Datetime(string="Changed On", default=fields.Datetime.now)
    changed_by = fields.Many2one('res.users', string="Changed By", default=lambda self: self.env.user)



class ProductProduct(models.Model):
    _inherit = "product.product"

    def write(self, vals):
        res = super().write(vals)
        if 'lst_price' in vals:
            for product in self:
                old_price = product.lst_price
                new_price = vals['lst_price']
                if old_price != new_price:
                    _logger.info("Product %s price changed from %s to %s", product.name, old_price, new_price)
                    self.env['product.price.log'].create({
                        'product_id': product.id,
                        'old_price': old_price,
                        'new_price': new_price,
                    })
        return res

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        if 'list_price' in vals:
            for template in self:
                old_price = template.list_price
                new_price = vals['list_price']
                for product in template.product_variant_ids:
                        self.env['product.price.log'].create({
                            'product_id': product.id,
                            'old_price': old_price,
                            'new_price': new_price,
                        })
        res = super().write(vals)

        return res
