# -*- coding: utf-8 -*-
from odoo import fields, models, api


class CoffeeZone(models.Model):
    _name = 'coffee.zone'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Zone'
    _rec_name = 'name'

    name = fields.Char(string='Zone Name', required=True, help="The administrative zone of the coffee origin.")
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.ref('base.et'), readonly=True)
    region_id = fields.Many2one('res.country.state', string='Region', required=True,
                                domain="[('country_id', '=', country_id)]",
                                help="The region this zone belongs to.")
    description = fields.Text(string='Description', help="A brief description of the zone.")


class CoffeeWoreda(models.Model):
    _name = 'coffee.woreda'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Woreda'
    _rec_name = 'name'

    name = fields.Char(string='Woreda Name', required=True,
                       help="The administrative woreda (district) of the coffee origin.")
    zone_id = fields.Many2one('coffee.zone', string='Zone', required=True, help="The zone this woreda belongs to.")
    description = fields.Text(string='Description', help="A brief description of the woreda.")
    population = fields.Integer(string='Population', help="The population of the woreda.")
    area_sq_km = fields.Float(string='Area (sq km)', help="The area of the woreda in square kilometers.")

    # New fields for agricultural data
    soil_type = fields.Selection([
        ('nitisols', 'Nitisols'),
        ('vertisols', 'Vertisols'),
        ('andosols', 'Andosols'),
        ('cambisols', 'Cambisols'),
        ('luvisols', 'Luvisols'),
    ], string='Soil Type', help="The primary soil type found in this woreda.")
    altitude = fields.Integer(string='Altitude (meters)')
    weather = fields.Char(string='Climate',
                          help="Current or typical weather conditions (e.g., 'Sunny', 'Rainy').")
    avg_temperature_c = fields.Float(string='Avg. Temperature (°C)',
                                     help="The average annual temperature in Celsius.")
    annual_rainfall_mm = fields.Float(string='Annual Rainfall (mm)', help="The average annual rainfall in millimeters.")
