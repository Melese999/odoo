# -*- coding: utf-8 -*-
from odoo import fields, models, api


class CoffeeContractLine(models.Model):
    _name = 'coffee.contract.line'
    _description = 'Coffee Contract Line'

    contract_id = fields.Many2one(
        'coffee.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('categ_id.name', '=', 'Processed Coffee')]"
    )
    name = fields.Char(
        string='Description'
    )
    quantity_tons = fields.Float(
        string='Quantity (Tons)',
        required=True,
        digits='Product Unit of Measure'
    )
    quantity_kg = fields.Float(
        string='Quantity (KG)',
        compute='_compute_quantity_kg',
        store=True
    )
    unit_price_usd_per_lb = fields.Float(
        string='Unit Price (USD/LB)',
        required=True,
        digits='Product Price'
    )
    price_per_kg = fields.Float(
        string='Unit Price (USD/KG)',
        compute='_compute_price_per_kg',
        store=True
    )
    subtotal_usd = fields.Float(
        string='Subtotal (USD)',
        compute='_compute_subtotal_usd',
        store=True
    )
    state = fields.Selection(
        related='contract_id.state',
        string='Contract Status',
        store=True,
        readonly=True
    )

    @api.depends('quantity_tons')
    def _compute_quantity_kg(self):
        for line in self:
            line.quantity_kg = line.quantity_tons * 1000.0

    @api.depends('unit_price_usd_per_lb')
    def _compute_price_per_kg(self):
        LB_PER_KG = 2.20462
        for line in self:
            line.price_per_kg = line.unit_price_usd_per_lb * LB_PER_KG

    @api.depends('quantity_kg', 'price_per_kg')
    def _compute_subtotal_usd(self):
        for line in self:
            line.subtotal_usd = line.quantity_kg * line.price_per_kg

    def name_get(self):
        result = []
        for line in self:
            name = f"{line.product_id.display_name or ''} - {line.quantity_tons:.2f}T @ {line.unit_price_usd_per_lb:.2f} USD/LB"
            result.append((line.id, name))
        return result