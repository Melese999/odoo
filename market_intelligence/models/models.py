# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MarketIntelligenceLine(models.Model):
    _name = 'market_intelligence.market_intelligence_line'
    _description = 'Market Intelligence Lines'

    product_id = fields.Many2one("product.product", required=True)
    unit_price = fields.Float(digits=(16,3))
    unit_price_uom_id = fields.Many2one("uom.uom")
    stock = fields.Float(digits=(16,5))
    stock_uom_id = fields.Many2one("uom.uom")
    description = fields.Text()
    market_intelligence_id = fields.Many2one("market_intelligence.market_intelligence")

    mi_date = fields.Date(
        string="Market Date",
        related="market_intelligence_id.date",
        store=True,   # important! must be stored to use in graph/read_group
        readonly=True
    )

    @api.model
    def get_price_trend(self, competitor_id=None, product_ids=None, date_from=fields.Date.mo, date_to=None):
        """
        Returns aggregated price trend for selected product(s) and competitor over time.
        """
        domain = []

        # Filter by competitor
        if competitor_id:
            domain.append(('market_intelligence_id.competitor_id', '=', competitor_id))

        # Filter by products
        if product_ids:
            domain.append(('product_id', 'in', product_ids))

        # Filter by date range
        if date_from:
            domain.append(('market_intelligence_id.date', '>=', date_from))
        if date_to:
            domain.append(('market_intelligence_id.date', '<=', date_to))

        # Group by date and product
        data = self.read_group(
            domain=domain,
            fields=['unit_price', 'product_id', 'market_intelligence_id.date'],
            groupby=['market_intelligence_id.date', 'product_id'],
            orderby='market_intelligence_id.date ASC'
        )

        # Format data for graph or chart
        trend_data = []
        for rec in data:
            trend_data.append({
                'date': rec['market_intelligence_id.date'],
                'product': rec['product_id'][1] if rec['product_id'] else 'Unknown',
                'unit_price': rec['unit_price'],
            })

        return trend_data


class MarketIntelligence(models.Model):
    _name = 'market_intelligence.market_intelligence'
    _description = 'Market Intelligence'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="MI Number", required=True, copy=False, readonly=True,
                       index=True, default="New", tracking=True)
    date = fields.Date("Market date", default=fields.Date.today())
    competitor_id = fields.Many2one("competitor.competitor", string="Competitor")
    company_ids = fields.Many2many(
        "res.company", 
        string="Companies", 
        required=True,
        help="Link market intelligence to your companies."
    )
    line_ids = fields.One2many("market_intelligence.market_intelligence_line", "market_intelligence_id")
    remark = fields.Text()

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].sudo().next_by_code("market_intelligence.market_intelligence") or "New"
        return super(MarketIntelligence, self).create(vals)
