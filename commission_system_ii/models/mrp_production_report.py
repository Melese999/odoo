# models/mrp_production_report.py
from odoo import models, fields, api
from datetime import datetime


class MrpProductionReport(models.AbstractModel):
    _name = 'report.mrp.grouped_production_report'
    _description = 'Grouped Manufacturing Orders Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate report values for grouped manufacturing orders"""
        productions = self.env['mrp.production'].browse(docids)

        # Group productions by their sale order
        grouped_data = {}
        for production in productions:
            sale_order = self._get_sale_order(production)
            if sale_order:
                if sale_order.id not in grouped_data:
                    grouped_data[sale_order.id] = {
                        'sale_order': sale_order,
                        'productions': []
                    }
                grouped_data[sale_order.id]['productions'].append(production)

        # Convert to sorted list
        sorted_groups = sorted(grouped_data.values(), key=lambda x: x['sale_order'].name)

        return {
            'doc_ids': docids,
            'doc_model': 'mrp.production',
            'groups': sorted_groups,
            'get_custom_fields': self._get_custom_fields,
            'current_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }

    def _get_sale_order(self, production):
        """Extract sale order from production origin"""
        if production.origin:
            # Try to find sale order by name
            sale_orders = self.env['sale.order'].search([('name', '=', production.origin)])
            if sale_orders:
                return sale_orders[0]

            # Try to find sale order by reference in origin
            if 'SO' in production.origin:
                try:
                    so_ref = production.origin.split('SO')[-1].split()[0]
                    sale_order = self.env['sale.order'].search([('name', 'ilike', f'SO{so_ref}')])
                    if sale_order:
                        return sale_order[0]
                except:
                    pass
        return False

    def _get_custom_fields(self, production):
        """Get custom fields for display"""
        return {
            'length': production.length or 0,
            'weight': production.weight or 0,
            'pitch': production.pitch or 0,
            'total_length': production.total_length or 0,
            'total_weight': production.total_weight or 0,
            'sketch_attachment_ids': production.sketch_attachment_ids or 0,

        }

