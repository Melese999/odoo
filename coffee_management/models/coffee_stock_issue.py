# coffee_system/models/coffee_stock_issue.py
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class CoffeeStockIssue(models.Model):
    _name = 'coffee.stock.issue'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Stock Issue'
    _rec_name = 'receiving_no_id'

    date = fields.Date(string='Date', default=fields.Date.today(), required=True)

    # === THE OBSOLETE FIELD BELOW HAS BEEN REMOVED ===
    # type_of_coffee_id = fields.Many2one('coffee.type', string='Type of Coffee', required=True)

    receiving_no_id = fields.Many2one(
        'coffee.stock.receiving',
        string='Receiving No. (GRN)',
        required=True,
        domain="[('state', '=', 'done')]"
    )
    # The product now comes directly from the selected GRN (Receiving record)
    product_id = fields.Many2one(
        related='receiving_no_id.product_id',
        string='Coffee Product',
        store=True,
        readonly=True
    )
    contract_id = fields.Many2one('coffee.contract', string='Related Contract')

    order_no = fields.Char(string='Order No.')
    certificate_no = fields.Char(string='Certificate No.')
    weight_bridge_kg = fields.Float(string='Weight Bridge Kg')
    medium_weight_kg = fields.Float(string='Medium Weight Kg')
    issued_bags = fields.Integer(string='Issued (Bag)', required=True)
    issued_kg = fields.Float(string='Issued (Kg)', required=True)
    remark = fields.Text(string='Remark')
    prepared_by = fields.Many2one(
        'res.users',
        string='Prepared By',
        default=lambda self: self.env.user,
        readonly=True
    )
    received_by = fields.Char(string='Received By')
    approved_by = fields.Char(string='Approved By')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.constrains('issued_bags', 'issued_kg')
    def _check_issued_quantities(self):
        for record in self:
            if record.issued_bags <= 0 or record.issued_kg <= 0:
                raise ValidationError(_("Issued Bags and KG must be greater than zero."))

    # === THE OBSOLETE ONCHANGE METHOD BELOW HAS BEEN REMOVED ===
    # It was causing the error because it referenced deleted models.
    # @api.onchange('receiving_no_id')
    # def _onchange_receiving_no_id(self):
    #     pass

    def action_issue_stock(self):
        self.ensure_one()

        if not self.product_id or not self.receiving_no_id.location_id:
            raise UserError(_("Product or the source location from the original GRN is not specified."))

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id', '=', self.receiving_no_id.warehouse_id.id)
        ], limit=1)

        if not picking_type:
            raise UserError(_("No 'Delivery Orders' operation type found for the warehouse linked to the GRN."))

        source_location_id = self.receiving_no_id.location_id
        dest_location_id = self.env.ref('stock.stock_location_customers')
        partner = self.contract_id.buyer_id if self.contract_id else False

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': partner.id if partner else False,
            'location_id': source_location_id.id,
            'location_dest_id': dest_location_id.id,
            'origin': self.contract_id.contract_number if self.contract_id else self.receiving_no_id.grn,
            'note': f"Coffee Issue from GRN: {self.receiving_no_id.grn}",
        })

        stock_move = self.env['stock.move'].create({
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.issued_kg,
            'product_uom': self.product_id.uom_id.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })

        picking.action_confirm()

        # In Odoo 17, 'quantity' is the correct field name for 'quantity' on stock.move.line
        # Some versions might still use quantity, but 'quantity' is preferred.
        if hasattr(stock_move.move_line_ids, 'quantity'):
            stock_move.move_line_ids.write({'quantity': self.issued_kg})
        else:
            stock_move.move_line_ids.write({'quantity': self.issued_kg})

        picking.button_validate()

        self.state = 'done'

        if self.contract_id:
            self.contract_id._compute_delivered_quantity()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Stock Issued Successfully'),
                'message': f"Delivery Order for {self.issued_kg} KG of {self.product_id.name} has been processed.",
                'sticky': False,
            }
        }
