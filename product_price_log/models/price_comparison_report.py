from odoo import models, fields, api

class PriceComparisonReport(models.Model):
    _name = "price.comparison.report"
    _description = "Price vs Competitor Report"
    _auto = False  # SQL view, not a real table
    _order = "date asc"

    date = fields.Date("Date")
    product_id = fields.Many2one("product.product", string="Product")
    competitor_id = fields.Many2one("competitor.competitor", string="Competitor")
    source = fields.Selection([
        ('your', 'AMG Price'),
        ('competitor', 'Competitor Price')
    ], string="Source")
    price = fields.Float("Price")

    def init(self):
        """SQL View: merge product price log + competitor price"""
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW price_comparison_report AS (
                SELECT * FROM (
                    -- Your product price log
                    SELECT
                        ppl.id as id,
                        ppl.changed_date::date as date,
                        ppl.product_id,
                        NULL::int as competitor_id,
                        'your'::varchar as source,
                        ppl.new_price as price
                    FROM product_price_log ppl

                    UNION ALL

                    -- Competitor market intelligence
                    SELECT
                        mil.id + 1000000 as id,
                        mil.mi_date as date,
                        mil.product_id,
                        mil.competitor_id,
                        'competitor'::varchar as source,
                        mil.unit_price as price
                    FROM market_intelligence_market_intelligence_line mil
                ) AS all_data
                ORDER BY date ASC, id ASC
            )
    """)
