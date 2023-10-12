from odoo import models, fields, api
from odoo.exceptions import UserError

class product_template(models.Model):
    _inherit = 'product.template'
    
    product_spt_id = fields.Many2one(
        comodel_name="product_spt",
        string='Related to TTRX2 product',
        compute="_compute_ttrx_product"
    )
    identifier_duns = fields.Char(
        related="product_spt_id.identifier_duns",
        string="DUNS Code")
    identifier_hin = fields.Char(
        related="product_spt_id.identifier_hin",
        string="HIN Code")
    identifier_us_dea = fields.Char(
        related="product_spt_id.identifier_us_dea",
        string="US DEA Code")
    identifier_us_ndc = fields.Char(
        related="product_spt_id.identifier_us_ndc",
        string="US NDC Code")
    identifier_br_cnes = fields.Char(
        related="product_spt_id.identifier_br_cnes",
        string="BR CNES Code")
    identifier_br_cnjp = fields.Char(
        related="product_spt_id.identifier_br_cnjp",
        string="BR CNPJ Code")
    identifier_br_cpf = fields.Char(
        related="product_spt_id.identifier_br_cpf",
        string="BR CPF Code")
    identifier_br_profegnbr = fields.Char(
        related="product_spt_id.identifier_br_profegnbr",
        string="BR Profeg NBR Code")
    identifier_ca_din = fields.Char(
        related="product_spt_id.identifier_ca_din",
        string="CA DIN Code")

    def _compute_ttrx_product(self):
        if self.ttr_uuid:
            product_id = self.env['product.spt'].search([('uuid','=', self.ttr_uuid)])
            self.product_spt_id = product_id

class product_product(models.Model):
    _inherit = 'product.product'
    
    product_spt_id = fields.Many2one(
        comodel_name="product_spt",
        string='Related to TTRX2 product',
        compute="_compute_ttrx_product"
    )
    identifier_duns = fields.Char(
        related="product_spt_id.identifier_duns",
        string="DUNS Code")
    identifier_hin = fields.Char(
        related="product_spt_id.identifier_hin",
        string="HIN Code")
    identifier_us_dea = fields.Char(
        related="product_spt_id.identifier_us_dea",
        string="US DEA Code")
    identifier_us_ndc = fields.Char(
        related="product_spt_id.identifier_us_ndc",
        string="US NDC Code")
    identifier_br_cnes = fields.Char(
        related="product_spt_id.identifier_br_cnes",
        string="BR CNES Code")
    identifier_br_cnjp = fields.Char(
        related="product_spt_id.identifier_br_cnjp",
        string="BR CNPJ Code")
    identifier_br_cpf = fields.Char(
        related="product_spt_id.identifier_br_cpf",
        string="BR CPF Code")
    identifier_br_profegnbr = fields.Char(
        related="product_spt_id.identifier_br_profegnbr",
        string="BR Profeg NBR Code")
    identifier_ca_din = fields.Char(
        related="product_spt_id.identifier_ca_din",
        string="CA DIN Code")

    tracktrace_is = fields.Boolean('Is TrackTraceRx2',compute="_compute_tracktrace", store=False)
    product_spt_id = fields.Many2one('product.spt',string='Product SPT',compute="_compute_tracktrace", store=False)
    
    def _compute_tracktrace(self):
        for reg in self:
            reg.product_spt_id = self.env['product.spt'].search([('product_id','=',reg.id)],limit=1)
            reg.tracktrace_is = bool(reg.product_spt_id)

    def _compute_ttrx_product(self):
        if self.ttr_uuid:
            product_id = self.env['product.spt'].search([('uuid','=', self.ttr_uuid)])
            self.product_spt_id = product_id