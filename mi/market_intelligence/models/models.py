# -*- coding: utf-8 -*-

from odoo import models, fields, api





class MarketIntelligenceLine(models.Model):
    _name = 'market_intelligence.market_intelligence_line'
    _description = 'market_intelligence lines'

    product_id = fields.Many2one("product.product")
    unit_price = fields.Float(digits=(16,3))
    unit_price_uom_id = fields.Many2one("uom.uom")
    stock =  fields.Float(digits=(16,5))
    stock_uom_id = fields.Many2one("uom.uom")
    description = fields.Text()
    market_intelligence_id = fields.Many2one("market_intelligence.market_intelligence")


class MarketIntelligence(models.Model):
    _name = 'market_intelligence.market_intelligence'
    _description = 'market intelligence'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="MI Number", required=True, copy=False, readonly=True,
                       index=True, default="New",tracking=True)
    date = fields.Date("Market date",default=fields.Date.today())
    competitor_id = fields.Many2one("competitor.competitor")
    company_ids = fields.Many2many(
        "res.company", 
        string="Companies", 
        required=True,
        help="Link market intelligence to your companies."
    )
    line_ids = fields.One2many("market_intelligence.market_intelligence_line","market_intelligence_id")
    remark = fields.Text()
   
    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].sudo().next_by_code("market_intelligence.market_intelligence") or "New"
        return super(MarketIntelligence, self).create(vals)


