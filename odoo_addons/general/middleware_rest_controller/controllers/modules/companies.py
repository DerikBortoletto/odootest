# -*- coding: utf-8 -*-
from odoo import http


class Companies(http.Controller):
    def __init__(self, *, company_id=None, user_id=None) -> None:
        self.company_id = company_id
        self.user_id = user_id
        self.request = http.request
        pass

    def get_company_name(self, company_id=None):
        company_name = None
        if bool(company_id):
            company = self.request.env["res.company"].sudo().search([("id", "=", int(company_id))])
            if bool(company):
                company_name = company[-1].name
        return company_name