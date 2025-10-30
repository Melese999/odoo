from odoo import models, fields, api


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    def _run_manufacture(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        """Override to pass dimensional data to manufacturing order creation"""
        # Call parent method
        production = super(ProcurementGroup, self)._run_manufacture(
            product_id, product_qty, product_uom, location_id, name, origin, values)

        # Pass dimensional data to the manufacturing order
        if production and values:
            dimensional_data = {
                'length': values.get('length', 0.0),
                'weight': values.get('weight', 0.0),
                'pitch': values.get('pitch', 0.0),
                'total_length': values.get('total_length', 0.0),
                'total_weight': values.get('total_weight', 0.0),
            }
            production.write(dimensional_data)

            # Also link to sale order line if available
            if values.get('sale_line_id'):
                production.sale_line_id = values['sale_line_id']

        return production