# -*- coding: utf-8 -*-
# from odoo import http


# class Competitor(http.Controller):
#     @http.route('/competitor/competitor', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/competitor/competitor/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('competitor.listing', {
#             'root': '/competitor/competitor',
#             'objects': http.request.env['competitor.competitor'].search([]),
#         })

#     @http.route('/competitor/competitor/objects/<model("competitor.competitor"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('competitor.object', {
#             'object': obj
#         })

