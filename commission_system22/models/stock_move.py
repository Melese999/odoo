from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    length = fields.Float(string="Unit Length (m)", digits='Product Unit of Measure')
    weight = fields.Float(string="Unit Weight (kg)", digits='Product Unit of Measure')
    pitch = fields.Float(string="Pitch")
    total_length = fields.Float(string="Total Length (m)", digits='Product Unit of Measure')
    total_weight = fields.Float(string="Total Weight (kg)", digits='Product Unit of Measure')

    def _action_confirm(self, merge=True, merge_into=False):
        """Override to ensure dimensional data is passed to MO"""
        # First, ensure we have dimensional data from sale line if available
        for move in self:
            print(move)
            # if move.sale_line_id and not any([move.length, move.weight, move.pitch]):
            #     move.write({
            #         'length': move.sale_line_id.length,
            #         'weight': move.sale_line_id.weight,
            #         'pitch': move.sale_line_id.pitch,
            #         'total_length': move.sale_line_id.total_length,
            #         'total_weight': move.sale_line_id.total_weight,
            #     })
            #     _logger.info("Copied dimensional data from sale line %s to move %s",
            #                  move.sale_line_id.id, move.id)

        result = super(StockMove, self)._action_confirm(merge=merge, merge_into=merge_into)

        return result

        # Now ensure manufacturing orders have the dimensional data
        for move in self:
            if move.production_id and move.sale_line_id:
                # Check if MO already has the correct data
                current_data = {
                    'length': move.production_id.length,
                    'weight': move.production_id.weight,
                    'pitch': move.production_id.pitch,
                }

                expected_data = {
                    'length': move.sale_line_id.length,
                    'weight': move.sale_line_id.weight,
                    'pitch': move.sale_line_id.pitch,
                    'total_length': move.sale_line_id.total_length,
                    'total_weight': move.sale_line_id.total_weight,
                    'sale_line_id': move.sale_line_id.id,
                }

                # Only update if data is different
                if current_data != expected_data:
                    move.production_id.write(expected_data)
                    _logger.info("Updated MO %s with dimensional data from sale line %s",
                                 move.production_id.id, move.sale_line_id.id)

        return result