from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    location_id = fields.Many2one(
        'stock.location',
        string='Production Location',
        help='Plant/production location for visibility and filtering (tracking only).'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to assign location_id automatically:
        - From sale_order_id if present
        - From origin if it matches a Sale Order
        - Otherwise from user's default production_location_id
        """
        for vals in vals_list:
            # Try to detect from sale_order_id (explicit)
            sale_order = False
            if vals.get('sale_order_id'):
                sale_order = self.env['sale.order'].browse(vals['sale_order_id'])
            elif vals.get('origin'):
                # Try matching the origin with sale order name
                sale_order = self.env['sale.order'].search([('name', '=', vals['origin'])], limit=1)

            # Assign location from Sale Order
            if sale_order and sale_order.location_id:
                vals['location_id'] = sale_order.location_id.id

            # Fallback: assign user's default production location if any
            elif not vals.get('location_id') and self.env.user.production_location_id:
                vals['location_id'] = self.env.user.production_location_id.id

        productions = super().create(vals_list)
        return productions
