# -*- coding: utf-8 -*-
# from odoo import http


# class ScrumAgileFramework(http.Controller):
#     @http.route('/scrum_agile_framework/scrum_agile_framework/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/scrum_agile_framework/scrum_agile_framework/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('scrum_agile_framework.listing', {
#             'root': '/scrum_agile_framework/scrum_agile_framework',
#             'objects': http.request.env['scrum_agile_framework.scrum_agile_framework'].search([]),
#         })

#     @http.route('/scrum_agile_framework/scrum_agile_framework/objects/<model("scrum_agile_framework.scrum_agile_framework"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('scrum_agile_framework.object', {
#             'object': obj
#         })
