# -*- coding: utf-8 -*-
# from odoo import http


# class CommissionSystem(http.Controller):
#     @http.route('/commission_system/commission_system', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/commission_system/commission_system/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('commission_system.listing', {
#             'root': '/commission_system/commission_system',
#             'objects': http.request.env['commission_system.commission_system'].search([]),
#         })

#     @http.route('/commission_system/commission_system/objects/<model("commission_system.commission_system"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('commission_system.object', {
#             'object': obj
#         })

from odoo import http
from odoo.http import request


class CommissionSystemController(http.Controller):

    @http.route('/commission_system/test', type='http', auth='none')
    def test_route(self, **kwargs):
        return request.make_response(
            "Commission System Test Route - Working!",
            headers=[('Content-Type', 'text/plain')]
        )