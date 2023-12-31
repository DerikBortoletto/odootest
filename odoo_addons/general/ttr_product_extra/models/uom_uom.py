
from odoo import api, fields, models


class Uom(models.Model):
    _inherit = "uom.uom"

    code = fields.Char(string="Code", size=6)
    alternative_ids = fields.One2many("uom.uom.alternative", "uom_id", string="Alternative names")

    def _get_code_domain(self, sub_domain, domain):
        code_operator = sub_domain[1]
        code_value = sub_domain[2]
        alternative = (self.env["uom.uom.alternative"].search([("code", code_operator, code_value)]).mapped("uom_id"))
        domain = [
            ("id", "in", alternative.ids)
            if x[0] == "code" and x[2] == code_value and alternative.ids
            else x
            for x in domain
        ]
        return domain

    @api.model
    def search(self, domain, *args, **kwargs):
        for sub_domain in list(filter(lambda x: x[0] == "code", domain)):
            domain = self._get_code_domain(sub_domain, domain)
        return super(Uom, self).search(domain, *args, **kwargs)
