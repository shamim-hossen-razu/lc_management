# -*- coding: utf-8 -*-
# from odoo import http


# class LcManagement(http.Controller):
#     @http.route('/lc_management/lc_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lc_management/lc_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('lc_management.listing', {
#             'root': '/lc_management/lc_management',
#             'objects': http.request.env['lc_management.lc_management'].search([]),
#         })

#     @http.route('/lc_management/lc_management/objects/<model("lc_management.lc_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lc_management.object', {
#             'object': obj
#         })

