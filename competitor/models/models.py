# -*- coding: utf-8 -*-
from odoo import models, fields

class CompetitorIndustry(models.Model):
    _name = "competitor.industry"
    _description = "Types of Competitor Industries"

    name = fields.Char(
        "Name", 
        required=True, 
        help="Enter the competitor's industry name.",
        tracking=True
    )
    active = fields.Boolean(
        "Active", 
        default=True, 
        help="Uncheck if this industry is not active."
    )


class Competitor(models.Model):
    _name = 'competitor.competitor'
    _description = 'Competitor'

    name = fields.Char(
        "Name", 
        required=True, 
        help="Enter the competitor's full name.",
        tracking=True
    )
    description = fields.Text(
        "Description", 
        help="Provide a brief description of the competitor."
    )
    website = fields.Char(
        "Website", 
        help="Enter the competitor's website URL. Example: https://www.example.com"
    )
    country_id = fields.Many2one(
        "res.country", 
        "Country", 
        required=True,
        default=69,
        help="Select the country where the competitor is based."
    )
    industry_ids = fields.Many2many(
        "competitor.industry", 
        string="Industries",
        help="Select industries this competitor belongs to."
    )
    phone = fields.Char(
        "Phone", 
        required=True, 
        help="Competitor's contact phone number."
    )
    email = fields.Char(
        "Email", 
        help="Competitor's official email."
    )
    active = fields.Boolean(
        "Active", 
        default=True
    )
    company_ids = fields.Many2many(
        "res.company", 
        string="Companies", 
        required=True,
        help="Link competitor to your companies."
    )
    notes = fields.Html("Notes")
    latitude = fields.Float("Latitude", digits=(12, 6))
    longitude = fields.Float("Longitude", digits=(12, 6))
