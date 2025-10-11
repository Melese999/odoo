from odoo import models
import logging

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id,
                               values):
        """Override to include dimensional data in move values"""
        move_values = super(StockRule, self)._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin, company_id, values)

        # Check if values is a dictionary and has sale_line_id
        if isinstance(values, dict) and values.get('sale_line_id'):
            sale_line = self.env['sale.order.line'].browse(values['sale_line_id'])
            move_values.update({
                'length': sale_line.length,
                'weight': sale_line.weight,
                'pitch': sale_line.pitch,
                'total_length': sale_line.total_length,
                'total_weight': sale_line.total_weight,
            })
            _logger.info("Adding dimensional data to move from sale line %s", sale_line.id)

        return move_values

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values,
                         bom):
        """Override manufacturing order creation to include dimensional data"""
        mo_vals = super(StockRule, self)._prepare_mo_vals(
            product_id, product_qty, product_uom, location_id, name, origin, company_id, values, bom)

        # Check if values is a dictionary and has sale_line_id
        if isinstance(values, dict) and values.get('sale_line_id'):
            sale_line = self.env['sale.order.line'].browse(values['sale_line_id'])
            mo_vals.update({
                'sale_line_id': sale_line.id,
                'length': sale_line.length,
                'weight': sale_line.weight,
                'pitch': sale_line.pitch,
                'total_length': sale_line.total_length,
                'total_weight': sale_line.total_weight,
            })
            _logger.info("Creating MO with dimensional data from sale line %s", sale_line.id)

        return mo_vals