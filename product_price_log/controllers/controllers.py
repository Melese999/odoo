# -*- coding: utf-8 -*-
# from odoo import http


# class ProductPriceLog(http.Controller):
#     @http.route('/product_price_log/product_price_log', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_price_log/product_price_log/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_price_log.listing', {
#             'root': '/product_price_log/product_price_log',
#             'objects': http.request.env['product_price_log.product_price_log'].search([]),
#         })

#     @http.route('/product_price_log/product_price_log/objects/<model("product_price_log.product_price_log"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_price_log.object', {
#             'object': obj
#         })

