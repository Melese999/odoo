# -*- coding: utf-8 -*-
# from odoo import http


# class CoffeeSystem(http.Controller):
#     @http.route('/coffee_system/coffee_system', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/coffee_system/coffee_system/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('coffee_system.listing', {
#             'root': '/coffee_system/coffee_system',
#             'objects': http.request.env['coffee_system.coffee_system'].search([]),
#         })

#     @http.route('/coffee_system/coffee_system/objects/<model("coffee_system.coffee_system"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('coffee_system.object', {
#             'object': obj
#         })

