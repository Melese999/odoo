import logging
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class CoffeeStockReceiving(models.Model):
    _name = 'coffee.stock.receiving'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Stock Receiving'
    _rec_name = 'grn'

    arrival_id = fields.Many2one(
        'coffee.arrival',
        string='Arrival Record',
        required=True,
        ondelete='cascade',
        help="The related Coffee Arrival record for which this stock is being received."
    )
    grn = fields.Char(
        string='Coffee Receiving No. (GRN)',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        help="Good Receiving Note number, automatically generated."
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        help="The warehouse where the coffee is being received."
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Block (Location)',
        required=True,
        domain="[('usage', '=', 'internal'), ('warehouse_id', '=', warehouse_id)]",
        help="The specific internal location (block) within the warehouse."
    )

    # === START OF REFACTORED CODE ===
    # The product is no longer manually selected here. It's inherited from the Arrival record.
    product_id = fields.Many2one(
        related='arrival_id.product_id',
        string='Coffee Product',
        store=True,
        readonly=True
    )
    # === END OF REFACTORED CODE ===

    received_bags = fields.Integer(
        string='Received Bags',
        required=True,
        help="The number of bags received."
    )
    received_kg = fields.Float(
        string='Received KG',
        required=True,
        digits='Product Unit of Measure',
        help="The weight in kilograms received."
    )

    # ... (Computed fields for stock balances are fine) ...
    beginning_balance_bags = fields.Integer(string='Beginning Balance (Bag)', compute='_compute_current_stock',
                                            store=True)
    beginning_balance_kg = fields.Float(string='Beginning Balance (KG)', compute='_compute_current_stock', store=True)
    issued_bags = fields.Integer(string='Issued (Bag)', compute='_compute_current_stock', store=True)
    issued_kg = fields.Float(string='Issued (KG)', compute='_compute_current_stock', store=True)
    current_stock_balance_bags = fields.Integer(string='Current Stock Balance (Bag)', compute='_compute_current_stock',
                                                store=True)
    current_stock_balance_kg = fields.Float(string='Current Stock Balance (KG)', compute='_compute_current_stock',
                                            store=True)

    # This related field is necessary for the search view's group_by filter.
    supplier_id = fields.Many2one(
        related='arrival_id.supplier_id',
        string='Supplier',
        store=True,
        readonly=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # === START OF REFACTORED CODE ===
    @api.onchange('arrival_id')
    def _onchange_arrival_id(self):
        """
        Automatically populates fields when an arrival record is selected.
        The product is now handled by the related field definition.
        We only need to populate the weight and bags.
        """
        if self.arrival_id and self.arrival_id.weight_history_id:
            self.received_bags = self.arrival_id.weight_history_id.num_of_bags
            self.received_kg = self.arrival_id.weight_history_id.coffee_tea_weight
        else:
            self.received_bags = 0
            self.received_kg = 0.0

    # === END OF REFACTORED CODE ===

    # @api.model
    # def create(self, vals):
    #     if vals.get('grn', 'New') == 'New':
    #         vals['grn'] = self.env['ir.sequence'].next_by_code('coffee.stock.receiving') or 'New'
    #     return super(CoffeeStockReceiving, self).create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('grn', 'New') == 'New':
                vals['grn'] = self.env['ir.sequence'].next_by_code('coffee.stock.receiving') or 'New'
        return super().create(vals_list)

    @api.constrains('received_bags', 'received_kg')
    def _check_received_quantities(self):
        for record in self:
            if record.received_bags <= 0 or record.received_kg <= 0:
                raise ValidationError(_("Received Bags and KG must be greater than zero."))

    # ... (action_receive_stock, action_create_manufacturing_order, and _compute_current_stock methods are fine as they were in previous responses) ...
    def action_receive_stock(self):
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id', '=', self.warehouse_id.id),
        ], limit=1)
        if not picking_type:
            raise UserError(_("No 'Receipts' operation type found for warehouse %s!") % self.warehouse_id.name)

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': self.arrival_id.supplier_id.id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.location_id.id,
            'origin': self.grn,
        })
        stock_move = self.env['stock.move'].create({
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.received_kg,
            'product_uom': self.product_id.uom_id.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        picking.action_confirm()
        for line in stock_move.move_line_ids:
            line.quantity = self.received_kg
        picking.button_validate()
        self.state = 'done'
        self.arrival_id.state = 'done'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Stock Received Successfully'),
                'message': f"GRN {self.grn} processed for {self.received_kg} KG.",
                'sticky': False,
            }
        }

    @api.depends('product_id', 'location_id', 'state')
    def _compute_current_stock(self):
        for record in self:
            if record.product_id and record.location_id:
                stock_quant = self.env['stock.quant'].search([
                    ('product_id', '=', record.product_id.id),
                    ('location_id', '=', record.location_id.id)
                ], limit=1)
                current_kg = stock_quant.quantity if stock_quant else 0.0
                record.current_stock_balance_kg = current_kg

                if hasattr(record.product_id, 'weight_per_bag') and record.product_id.weight_per_bag:
                    record.current_stock_balance_bags = int(current_kg / record.product_id.weight_per_bag)
                else:
                    record.current_stock_balance_bags = 0

                issued_records = self.env['coffee.stock.issue'].search([
                    ('product_id', '=', record.product_id.id),
                    ('state', '=', 'done'),
                ])
                total_issued_kg = sum(issue.issued_kg for issue in issued_records)
                total_issued_bags = sum(issue.issued_bags for issue in issued_records)
                record.issued_kg = total_issued_kg
                record.issued_bags = total_issued_bags

                if record.state == 'done':
                    record.beginning_balance_kg = record.current_stock_balance_kg - record.received_kg
                    record.beginning_balance_bags = record.current_stock_balance_bags - record.received_bags
                else:
                    record.beginning_balance_kg = record.current_stock_balance_kg
                    record.beginning_balance_bags = record.current_stock_balance_bags
            else:
                record.beginning_balance_bags = 0
                record.beginning_balance_kg = 0
                record.issued_bags = 0
                record.issued_kg = 0
                record.current_stock_balance_bags = 0
                record.current_stock_balance_kg = 0