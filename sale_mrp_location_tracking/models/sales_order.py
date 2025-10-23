from odoo import models, fields, api
from odoo.exceptions import AccessError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    location_id = fields.Many2one(
        'stock.location', string='Production Location',
        help='Production location/plant for tracking (does not affect stock moves).'
    )

    @api.model
    def default_get(self, fields_list):
        res = super(SaleOrder, self).default_get(fields_list)
        user_loc = self.env.user.production_location_id
        if user_loc:
            res.setdefault('location_id', user_loc.id)
        return res

    def write(self, vals):
        if 'location_id' in vals:
            allowed_group = self.env.ref(
                'sale_mrp_location_tracking.group_sales_location_manager',
                raise_if_not_found=False
            )
            if not allowed_group or (self.env.user and allowed_group not in self.env.user.groups_id):
                raise AccessError("You are not allowed to change the Production Location on a Sales Order.")

        # Proceed with the normal write
        res = super(SaleOrder, self).write(vals)

        # If the location_id was changed, update related manufacturing orders
        if 'location_id' in vals:
            for order in self:
                # Search by origin only, since sale_order_id doesn't exist on mrp.production
                mo_list = self.env['mrp.production'].search([
                    ('origin', '=', order.name)
                ])

                # Update only active (non-done/non-cancelled) MOs
                if mo_list:
                    mo_list.filtered(
                        lambda m: m.state not in ['done', 'cancel']
                    ).sudo().write({'location_id': order.location_id.id})

        return res
