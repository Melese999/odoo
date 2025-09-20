from odoo import models

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values, bom):
        mo_vals = super()._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name, origin, company_id, values, bom)
        if origin:
            picking = self.env['stock.picking'].search([('name', '=', origin)], limit=1)
            if picking and picking.coffee_contract_id:
                mo_vals['coffee_contract_id'] = picking.coffee_contract_id.id
        return mo_vals