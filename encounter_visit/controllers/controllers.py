# -*- coding: utf-8 -*-
# from odoo import http


# class EncounterVisit(http.Controller):
#     @http.route('/encounter_visit/encounter_visit', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/encounter_visit/encounter_visit/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('encounter_visit.listing', {
#             'root': '/encounter_visit/encounter_visit',
#             'objects': http.request.env['encounter_visit.encounter_visit'].search([]),
#         })

#     @http.route('/encounter_visit/encounter_visit/objects/<model("encounter_visit.encounter_visit"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('encounter_visit.object', {
#             'object': obj
#         })

