import re
import logging
# import base64
# from datetime import datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_company_address_field_names(self):
        partner_fields = super()._get_company_address_field_names()
        return partner_fields + [
                                 "legal_name",
                                 "cnpj_cpf",
                                 "inscr_est",
                                 "inscr_mun",
                                 "district",
                                 "city_id",
                                 "suframa",
                                 "rntrc",
                                 ]

    def _get_address_data(self):
        for company in self:
            company.city_id = company.partner_id.city_id
            company.district = company.partner_id.district
            company.number = company.partner_id.number

    def _get_br_data(self):
        """ Read the l10n_br specific functional fields. """
        for company in self:
            company.legal_name = company.partner_id.legal_name
            company.cnpj_cpf = company.partner_id.cnpj_cpf
            company.inscr_est = company.partner_id.inscr_est
            company.inscr_mun = company.partner_id.inscr_mun
            company.suframa = company.partner_id.suframa
            company.rntrc = company.partner_id.rntrc

    def _set_br_rntrc(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.rntrc = company.rntrc

    def _set_br_suframa(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.suframa = company.suframa

    def _set_br_legal_name(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.legal_name = company.legal_name

    def _set_br_cnpj_cpf(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.cnpj_cpf = company.cnpj_cpf

    def _set_br_inscr_est(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.inscr_est = company.inscr_est

    def _set_br_inscr_mun(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.inscr_mun = company.inscr_mun

    def _set_br_number(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.number = company.number

    def _set_br_district(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.district = company.district

    def _set_city_id(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.city_id = company.city_id

    # def _inverse_state_tax_number_ids(self):
    #     for company in self:
    #         state_tax_number_ids = self.env["state.tax.numbers"]
    #         for ies in company.state_tax_number_ids:
    #             state_tax_number_ids |= ies
    #         company.partner_id.state_tax_number_ids = state_tax_number_ids

    cnpj_cpf = fields.Char(compute=_get_br_data, inverse=_set_br_cnpj_cpf, size=18, string='CNPJ')
    inscr_est = fields.Char(compute=_get_br_data, inverse=_set_br_inscr_est, size=16, string='State Inscription')
    inscr_mun = fields.Char(compute=_get_br_data, inverse=_set_br_inscr_mun, size=18, string='Municipal Inscription')
    suframa = fields.Char(compute=_get_br_data, inverse=_set_br_suframa, size=18, string='Suframa')
    legal_name = fields.Char(compute=_get_br_data, inverse=_set_br_legal_name, size=128, string='Legal Name')
    city_id = fields.Many2one(compute=_get_address_data, inverse='_set_city_id', comodel_name='res.state.city', string="City")
    district = fields.Char(compute=_get_address_data, inverse='_set_br_district', size=32, string="District")
    number = fields.Char(compute=_get_address_data, inverse='_set_br_number', size=10, string="Number")
    rntrc = fields.Char(compute=_get_br_data, inverse='_set_br_rntrc', string='RNTRC', size=10, help="Registro Nacional de Transportadores Rodoviários de Carga")
    # state_tax_number_ids = fields.One2many(string="State Tax Numbers", comodel_name="state.tax.numbers", inverse_name="partner_id",  compute="_compute_address", inverse="_inverse_state_tax_number_ids")

    @api.onchange('cnpj_cpf')
    def onchange_mask_cnpj_cpf(self):
        if self.cnpj_cpf:
            val = re.sub('[^0-9]', '', self.cnpj_cpf)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                self.cnpj_cpf = cnpj_cpf

    @api.onchange('city_id')
    def onchange_city_id(self):
        """
            Ao alterar o campo city_id copia o nome
            do município para o campo city que é o campo nativo do módulo base
            para manter a compatibilidade entre os demais módulos que usam o
            campo city.
        """
        if self.city_id:
            self.city = self.city_id.name

    @api.onchange('zip')
    def onchange_mask_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                zip = "%s-%s" % (val[0:5], val[5:8])
                self.zip = zip

    @api.model
    def _fields_view_get(self, view_id=None, view_type="form", toolbar=False, submenu=False):
        res = super()._fields_view_get(view_id, view_type, toolbar, submenu)
        # if view_type == "form":
        #     res["arch"] = self._fields_view_get_address(res["arch"])
        return res
