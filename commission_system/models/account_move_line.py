
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

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

    @api.depends('quantity', 'length', 'weight')
    def _compute_total_dimensions(self):
        """Compute total dimensions based on quantity and unit dimensions"""
        for line in self:
            line.total_length = line.quantity * (line.length or 0.0)
            line.total_weight = line.quantity * (line.weight or 0.0)

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id',
                 'length', 'total_length', 'weight', 'total_weight',
                 'product_id.dimensional_uom_type')
    def _compute_totals(self):
        """
        Adjust price calculation based on the product's dimensional UOM type.
        """
        for line in self:
            if line.display_type != 'product':
                line.price_total = line.price_subtotal = 0.0
                continue

            # 1. Determine the effective quantity based on the pricing basis.
            effective_quantity = line.quantity
            if line.product_id.dimensional_uom_type == 'length':
                effective_quantity = line.total_length
            elif line.product_id.dimensional_uom_type == 'weight':
                effective_quantity = line.total_weight

            # 2. Apply discount to unit price
            line_discount_price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            # 3. Compute taxes using correct API (unit price + effective quantity)
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,  # unit price
                    currency=line.currency_id,
                    quantity=effective_quantity,  # dimensional quantity
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )
                line.price_subtotal = taxes_res['total_excluded']
                line.price_total = taxes_res['total_included']
            else:
                subtotal = effective_quantity * line_discount_price_unit
                line.price_total = line.price_subtotal = subtotal

    @api.depends('price_unit', 'quantity', 'length', 'weight', 'discount', 'tax_ids')
    def _compute_amount_currency(self):
        # 1. First, let the standard Odoo method compute the amounts
        #    for all lines, including the payment term line.
        super(AccountMoveLine, self)._compute_amount_currency()

        for line in self:
            # 2. Only apply your custom logic to lines of type 'product'
            if line.product_id.dimensional_uom_type in ('length', 'weight') and line.display_type == 'product':
                # Determine the effective quantity
                effective_quantity = line.quantity
                if line.product_id.dimensional_uom_type == 'length':
                    effective_quantity = line.total_length
                elif line.product_id.dimensional_uom_type == 'weight':
                    effective_quantity = line.total_weight

                # Apply discount to unit price
                line_discount_price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

                # Compute taxes using dimensional quantity
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    currency=line.currency_id,
                    quantity=effective_quantity,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )

                # Update the amounts on the product line
                line.amount_currency = taxes_res['total_excluded']
                line.balance = taxes_res['total_excluded']





