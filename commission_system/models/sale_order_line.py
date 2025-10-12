from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    price_type = fields.Selection(
        [('fixed', 'Fixed'), ('percentage', 'Percentage')],
        string="Price Type",
        default='fixed',
        help="Determines whether price is fixed or percentage-based"
    )

    dimensional_uom_type = fields.Selection(
        [('unit', 'Per Unit'),
         ('length', 'Per Meter'),
         ('weight', 'Per Kilogram')],
        string="Pricing Basis",
        default='unit',
        help="Determines how this product should be measured and priced"
    )

    length = fields.Float(
        string="Standard Length (m)",
        digits='Product Unit of Measure',
        default=1.0,
        help="Standard length per unit in meters"
    )

    weight = fields.Float(
        string="Standard Weight (kg)",
        digits='Product Unit of Measure',
        default=1.0,
        help="Standard weight per unit in kilograms"
    )

    @api.constrains('length', 'weight')
    def _check_dimension_values(self):
        """Validate dimension values at product level"""
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for product in self:
            if product.dimensional_uom_type == 'length' and float_compare(product.length, 0.0, precision) <= 0:
                raise ValidationError("Length must be positive for length-based products")
            if product.dimensional_uom_type == 'weight' and float_compare(product.weight, 0.0, precision) <= 0:
                raise ValidationError("Weight must be positive for weight-based products")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def has_available_route(self, route_type):
        """
        Check if the product has a specific route available
        :param route_type: string like 'manufacture', 'buy', 'mto', etc.
        :return: Boolean
        """
        self.ensure_one()

        # Get all possible routes for this product
        routes = self.route_ids | self.categ_id.route_ids

        # Also include warehouse routes
        warehouses = self.env['stock.warehouse'].search([])
        for warehouse in warehouses:
            routes |= warehouse.route_ids

        # Search for the specific route
        route = self.env['stock.route'].search([
            ('name', 'ilike', route_type)
        ], limit=1)

        return route in routes


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Dimensional fields
    length = fields.Float(
        string="Unit Length (m)",
        digits='Product Unit of Measure',
        help="Actual length per unit in meters"
    )

    total_length = fields.Float(
        string="Total Length (m)",
        compute='_compute_total_dimensions',
        store=True,
        digits='Product Unit of Measure',
        help="Calculated total length (Quantity × Unit Length)"
    )

    weight = fields.Float(
        string="Unit Weight (kg)",
        digits='Product Unit of Measure',
        help="Actual weight per unit in kilograms"
    )

    total_weight = fields.Float(
        string="Total Weight (kg)",
        compute='_compute_total_dimensions',
        store=True,
        digits='Product Unit of Measure',
        help="Calculated total weight (Quantity × Unit Weight)"
    )
    pitch = fields.Float(string="Pitch")
    effective_width = fields.Float(string="Effective Width")


    production_ids = fields.One2many(
        'mrp.production',
        'sale_line_id',
        string="Manufacturing Orders"
    )

    dimensional_uom_type = fields.Selection(
        related="product_id.dimensional_uom_type",
        store=True,
        readonly=True
    )

    sketch_count = fields.Integer(compute='_compute_sketch_count', string='Sketch Count')

    # This field will find attachments with 'sketch' in the name
    sketch_attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Sketch Attachments",
        compute='_compute_sketch_attachments',
        help="All sketches linked to this sale order line."
    )
    def duplicate(self):
        if self:
            self.copy(default={'order_id': self.order_id.id})
    def _compute_sketch_attachments(self):
        for line in self:
            line.sketch_attachment_ids = self.env['ir.attachment'].search([
                ('res_model', '=', 'sale.order.line'),
                ('res_id', '=', line.id),
                ('name', 'ilike', '%sketch%')
            ])

    def _compute_sketch_count(self):
        attachment_model = self.env['ir.attachment']
        for line in self:
            line.sketch_count = attachment_model.search_count([
                ('res_model', '=', 'sale.order.line'),
                ('res_id', '=', line.id),
                ('name', 'ilike', '%sketch%')
            ])

    def action_view_sketches(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        action['domain'] = [
            ('res_model', '=', 'sale.order.line'),
            ('res_id', '=', self.id),
            ('name', 'ilike', '%sketch%')
        ]
        action['context'] = {
            'default_res_model': 'sale.order.line',
            'default_res_id': self.id,
        }
        return action

    def action_open_sketch_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Design Sketch',
            'res_model': 'commission.sketch.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_line_id': self.id,
            }
        }

    @api.depends('product_uom_qty', 'length', 'weight')
    def _compute_total_dimensions(self):
        """Compute total dimensions based on quantity and unit dimensions"""
        for line in self:
            line.total_length = line.product_uom_qty * (line.length or 0.0)
            line.total_weight = line.product_uom_qty * (line.weight or 0.0)

    @api.onchange('product_id')
    def _onchange_product_id_dimensions(self):
        """Set default dimensions when product changes"""
        for line in self:
            if line.product_id:
                product = line.product_id
                line.length = product.length if product.dimensional_uom_type == 'length' else 0.0
                line.weight = product.weight if product.dimensional_uom_type == 'weight' else 0.0
            else:
                line.length = 0.0
                line.weight = 0.0

    @api.constrains('length', 'weight')
    def _check_dimension_values(self):
        """Validate dimension values at line level"""
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.product_id.dimensional_uom_type == 'length' and float_compare(line.length, 0.0, precision) <= 0:
                raise ValidationError("Length must be positive for length-based products")
            if line.product_id.dimensional_uom_type == 'weight' and float_compare(line.weight, 0.0, precision) <= 0:
                raise ValidationError("Weight must be positive for weight-based products")

    @api.depends('product_uom_qty', 'price_unit', 'tax_id', 'length', 'weight',
                 'product_id.dimensional_uom_type', 'discount')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            if line.product_id.dimensional_uom_type == 'length':
                quantity = line.product_uom_qty * line.length
            elif line.product_id.dimensional_uom_type == 'weight':
                quantity = line.product_uom_qty * line.weight
            else:
                quantity = line.product_uom_qty

            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                quantity,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id
            )

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        try:
            res.update({
                'length': self.length,
                'total_length': self.total_length,
                'weight': self.weight,
                'total_weight': self.total_weight,
            })
        except Exception as e:
            _logger.error("Error preparing invoice line dimensions for line %s: %s", self.id, str(e))
            raise
        return res

    def _prepare_procurement_values(self, group_id=False):
        """Override to include dimensional data in procurement values"""
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        values.update({
            'length': self.length,
            'weight': self.weight,
            'pitch': self.pitch,
            'total_length': self.total_length,
            'total_weight': self.total_weight,
        })
        _logger.info("Preparing procurement values with dimensions: %s", values)
        return values

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def write(self, values):
        return super().write(values)

    def unlink(self):
        return super().unlink()