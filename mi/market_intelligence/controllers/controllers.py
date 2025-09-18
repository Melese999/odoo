# -*- coding: utf-8 -*-
# from odoo import http


# class MarketIntelligence(http.Controller):
#     @http.route('/market_intelligence/market_intelligence', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/market_intelligence/market_intelligence/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('market_intelligence.listing', {
#             'root': '/market_intelligence/market_intelligence',
#             'objects': http.request.env['market_intelligence.market_intelligence'].search([]),
#         })

#     @http.route('/market_intelligence/market_intelligence/objects/<model("market_intelligence.market_intelligence"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('market_intelligence.object', {
#             'object': obj
#         })

