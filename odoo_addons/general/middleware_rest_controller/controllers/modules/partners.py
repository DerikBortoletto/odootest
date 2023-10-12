# -*- coding: utf-8 -*-
from odoo import http


class Partners(http.Controller):
    def __init__(self, *, company_id=None, user_id=None) -> None:
        self.company_id = company_id
        self.user_id = user_id
        self.request = http.request
        pass
    
    def create_partner(self, inputs):
        res = dict()
        payload = {
            "name": inputs["name"],
            "is_company": inputs["is_company"],
            "active": inputs["active"],
            "email": inputs["email"],
            "mobile": inputs["mobile"],
            "phone": inputs["phone"],
            "street": inputs["street"],
            # "street2": inputs["street2"],
            "city": inputs["city"],
            "state_id": int(inputs["state_id"]),
            "zip": inputs["zip"],
            "country_id": int(inputs["country_id"])
        }

        if "supplier_rank" in inputs:
            payload["supplier_rank"] = int(inputs["supplier_rank"])
        if "customer_rank" in inputs:
            payload["customer_rank"] = int(inputs["customer_rank"])

        supplier_created = self.request.env["res.partner"].sudo().create(payload)
        if bool(supplier_created):
            res["partner_id"] = supplier_created[-1].id
        else:
            raise Exception("Unable to create the partner!")
        return res

    def check_if_partner_exists(self, inputs):
        res = dict()
        _conds = list()
        _conds.append(("name", "=", inputs["name"]))
        partner = self.request.env["res.partner"].sudo().search(_conds)
        if bool(partner):
            res["partner_id"] = partner[-1].id
        else:
            raise Exception("No such partner exists!")
        return res

    def get_partner_name(self, partner_id, *, email=False):
        partner_name = None
        if bool(partner_id):
            partner = self.request.env["res.partner"].sudo().search([("id", "=", int(partner_id))])
            if bool(partner):
                partner_name = partner[-1].name
                if bool(email) and bool(partner[-1].email):
                    partner_name = partner_name + " <" + partner[-1].email + ">"
        return partner_name