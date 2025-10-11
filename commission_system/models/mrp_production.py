from odoo import models, fields, api
from datetime import datetime
import logging
import re

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line',
        readonly=True,
        copy=False,
        help="The sales order line that created this manufacturing order."
    )

    # Add an index for better performance
    _index = 'sale_line_id_index'

    length = fields.Float(
        string="Unit Length (m)",
        digits='Product Unit of Measure',
        help="Actual length per unit in meters, received from the sales order."
    )
    weight = fields.Float(
        string="Unit Weight (kg)",
        digits='Product Unit of Measure',
        help="Actual weight per unit in kilograms, received from the sales order."
    )
    pitch = fields.Float(
        string="Pitch",
        help="The pitch value for tile products, received from the sales order."
    )

    total_length = fields.Float(string='Total Length', compute='_compute_total_dimensions', store=True)
    total_weight = fields.Float(string='Total Weight', compute='_compute_total_dimensions', store=True)

    sketch_attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Design Sketches",
        help="Design sketches copied from the Sales Order line."
    )

    # Add this method to your MrpProduction model
    def get_sketch_urls(self):
        """Return list of sketch URLs for the report"""
        urls = []
        for attachment in self.sketch_attachment_ids:
            urls.append({
                'name': attachment.name,
                'url': '/web/content/%s?download=true' % attachment.id,
                'preview_url': '/web/image/%s' % attachment.id
            })
        return urls

    @api.depends('length', 'weight', 'pitch', 'product_qty')
    def _compute_total_dimensions(self):
        """Compute total dimensions based on quantity"""
        for production in self:
            production.total_length = production.length * production.product_qty
            production.total_weight = production.weight * production.product_qty

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to modify component quantities based on custom fields"""
        productions = super(MrpProduction, self).create(vals_list)

        for production in productions:
            if production.total_length or production.total_weight:
                production._update_component_quantities()

        return productions

    def write(self, vals):
        """Override write to update component quantities when custom fields change"""
        result = super(MrpProduction, self).write(vals)

        # Check if any of the custom fields were updated
        custom_fields_updated = any(
            field in vals for field in ['length', 'weight', 'pitch', 'total_length', 'total_weight', 'product_qty'])

        if custom_fields_updated:
            for production in self:
                production._update_component_quantities()

        return result

    def _update_component_quantities(self):
        """Update component quantities based on total_length or total_weight"""
        for move in self.move_raw_ids:
            # Get the original quantity from the BoM
            bom_line = self.env['mrp.bom.line'].search([
                ('bom_id', '=', self.bom_id.id),
                ('product_id', '=', move.product_id.id)
            ], limit=1)

            if bom_line:
                original_qty = bom_line.product_qty
                new_qty = original_qty

                # Apply total_length multiplier if total_length is specified
                if self.total_length and self.total_length != 0:
                    # Calculate based on total_length: (component_qty * total_length) / base_length
                    base_length = self.bom_id.product_qty  # Base quantity from BOM
                    if base_length and base_length != 0:
                        new_qty = (original_qty * self.total_length) / base_length

                # Apply total_weight multiplier if total_weight is specified
                elif self.total_weight and self.total_weight != 0:
                    # Calculate based on total_weight: (component_qty * total_weight) / base_weight
                    base_weight = self.bom_id.product_qty  # Base quantity from BOM
                    if base_weight and base_weight != 0:
                        new_qty = (original_qty * self.total_weight) / base_weight

                # Update the move quantity only if it changed
                if move.product_uom_qty != new_qty:
                    move.write({'product_uom_qty': new_qty})

    def action_print_grouped_report(self):
        """Action to print grouped manufacturing orders report"""
        return self.env.ref('commission_system.action_grouped_production_report').report_action(self)

    # In your MrpProduction class
    def action_print_simple_report(self):
        """Use the standard report action approach"""
        return self.env.ref('commission_system.action_simple_mo_report').report_action(self)

    def action_print_grouped_report_multi(self):
        """Action to print grouped report for multiple manufacturing orders"""
        return self.env.ref('commission_system.action_grouped_production_report').report_action(self)


class SimpleMOReport(models.AbstractModel):
    _name = 'report.commission_system.simple_mo_report_template'
    _description = 'Simple Manufacturing Orders Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Debug version to see what's happening"""
        _logger.info(f"Received docids: {docids}")

        productions = self.env['mrp.production'].browse(docids)
        _logger.info(f"Found {len(productions)} productions")

        # Just return all productions in a single group for testing
        groups = [{
            'origin': 'All Manufacturing Orders',
            'sale_order': False,
            'productions': productions
        }]

        # Log all productions
        for production in productions:
            _logger.info(f"MO: {production.name}, ID: {production.id}, Origin: {production.origin}")

        return {
            'doc_ids': docids,
            'doc_model': 'mrp.production',
            'groups': groups,
            'current_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'user': self.env.user,
        }

    def _get_sale_order(self, production):
        """Extract sale order from production origin with better logic"""
        if not production.origin:
            return False

        origin = production.origin.strip()

        # Method 1: Direct match by SO name
        sale_orders = self.env['sale.order'].search([('name', '=', origin)], limit=1)
        if sale_orders:
            return sale_orders[0]

        # Method 2: Try to extract SO number from origin
        so_patterns = [
            r'SO\d+',
            r'SO\s*\d+',
            r'Sales Order\s*\d+',
            r'Order\s*\d+'
        ]

        for pattern in so_patterns:
            matches = re.findall(pattern, origin, re.IGNORECASE)
            if matches:
                for match in matches:
                    # Clean up the match
                    so_ref = re.sub(r'[^0-9]', '', match)
                    if so_ref:
                        sale_orders = self.env['sale.order'].search([
                            ('name', 'ilike', so_ref)
                        ], limit=1)
                        if sale_orders:
                            return sale_orders[0]

        # Method 3: Search for any SO reference in origin
        sale_orders = self.env['sale.order'].search([
            ('name', 'ilike', origin)
        ], limit=1)

        if sale_orders:
            return sale_orders[0]

        return False