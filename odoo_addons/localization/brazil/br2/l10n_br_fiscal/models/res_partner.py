# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re
import base64
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError
from erpbrasil.assinatura import certificado as cert
from erpbrasil.base import misc

_logger = logging.getLogger(__name__)

from ..constants.fiscal import (
    FINAL_CUSTOMER,
    FINAL_CUSTOMER_NO,
    NFE_IND_IE_DEST,
    NFE_IND_IE_DEST_9,
    NFE_IND_IE_DEST_DEFAULT,
    TAX_FRAMEWORK,
    TAX_FRAMEWORK_NORMAL,
)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _default_fiscal_profile_id(self, is_company=False):
        """Define o valor padão para o campo tipo fiscal, por padrão pega
        o tipo fiscal para não contribuinte já que quando é criado um novo
        parceiro o valor do campo is_company é false"""
        return self.env["l10n_br_fiscal.partner.profile"].search(
            [("default", "=", True), ("is_company", "=", is_company)], limit=1
        )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        default=TAX_FRAMEWORK_NORMAL,
        tracking=True,
    )

    cnae_main_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cnae",
        domain=[("internal_type", "=", "normal")],
        string="Main CNAE",
    )

    ind_ie_dest = fields.Selection(
        selection=NFE_IND_IE_DEST,
        string="Contribuinte do ICMS",
        required=True,
        default=NFE_IND_IE_DEST_DEFAULT,
        tracking=True,
    )

    fiscal_profile_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.partner.profile",
        string="Fiscal Partner Profile",
        inverse="_inverse_fiscal_profile",
        domain="[('is_company', '=', is_company)]",
        default=_default_fiscal_profile_id,
        tracking=True,
    )

    ind_final = fields.Selection(
        selection=FINAL_CUSTOMER,
        string="Final Consumption Operation",
        default=FINAL_CUSTOMER_NO,
        tracking=True,
    )

    cnpj_cpf = fields.Char(
        tracking=True,
    )

    inscr_est = fields.Char(
        tracking=True,
    )

    inscr_mun = fields.Char(
        tracking=True,
    )

    is_company = fields.Boolean(
        tracking=True,
    )

    state_id = fields.Many2one(
        tracking=True,
    )

    city_id = fields.Many2one(
        tracking=True,
    )

    def _inverse_fiscal_profile(self):
        for p in self:
            p._onchange_fiscal_profile_id()

    @api.onchange("is_company")
    def _onchange_is_company(self):
        for p in self:
            p.fiscal_profile_id = p._default_fiscal_profile_id(p.is_company)

    @api.onchange("fiscal_profile_id")
    def _onchange_fiscal_profile_id(self):
        for p in self:
            if p.fiscal_profile_id:
                p.tax_framework = p.fiscal_profile_id.tax_framework
                p.ind_ie_dest = p.fiscal_profile_id.ind_ie_dest

    @api.onchange("ind_ie_dest")
    def _onchange_ind_ie_dest(self):
        for p in self:
            if p.ind_ie_dest == NFE_IND_IE_DEST_9:
                p.inscr_est = False
                p.state_tax_number_ids = False

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + [
            "tax_framework",
            "cnae_main_id",
            "ind_ie_dest",
            "fiscal_profile_id",
            "ind_final",
            "inscr_est",
            "inscr_mun",
        ]

    def action_check_sefaz(self):
        try:
            from pytrustnfe.nfe import consulta_cadastro
            from pytrustnfe.certificado import Certificado
        except ImportError:
            _logger.error('Cannot import pytrustnfe', exc_info=True)
            raise UserError('Falha ao consultar, verfique o log para maiores informações.')
        if self.cnpj_cpf and self.state_id:
            if self.state_id.code == 'AL':
                raise UserError(_('Alagoas doesn\'t have this service'))
            if self.state_id.code == 'RJ':
                raise UserError(_('Rio de Janeiro doesn\'t have this service'))
            company = self.env.company
            if not company.certificate_nfe_id and not company.certificate_nfe_id.is_valid:
                raise UserError(_('Configure the company\'s certificate and password'))
            # certificado = cert.Certificado(arquivo=self.company_id.certificate_nfe_id.file,
            #                                senha=self.company_id.certificate_nfe_id.password)

            # cert = company.with_context({'bin_size': False}).nfe_a1_file
            cert_pfx = base64.decodestring(company.certificate_nfe_id.file)
            # cert_pfx = company.certificate_nfe_id.file
            certificado = Certificado(cert_pfx, company.certificate_nfe_id.password)
            cnpj = re.sub('[^0-9]', '', self.cnpj_cpf)
            obj = {'cnpj': cnpj, 'estado': self.state_id.code}
            resposta = consulta_cadastro(certificado, obj=obj, ambiente=1, estado=self.state_id.ibge_code)

            if bool(resposta.get('object')):
                info = resposta['object'].getchildren()[0]
                info = info.infCons
                if info.cStat == 111 or info.cStat == 112:
                    if not self.inscr_est:
                        inscr = info.infCad.IE.text
                        if self.state_id.code == 'BA':
                            inscr = inscr.zfill(9)
                        self.inscr_est = inscr
                    if not self.cnpj_cpf:
                        cnpj_vl = re.sub('[^0-9]', '', info.infCad.CNPJ.text)
                        self.cnpj_cpf = "%s.%s.%s/" % (cnpj_vl[0:2], cnpj_vl[2:5], cnpj_vl[5:8])
    
                    def get_value(obj, prop):
                        if prop not in dir(obj):
                            return None
                        return getattr(obj, prop)
                    self.legal_name = get_value(info.infCad, 'xNome')
                    if "ender" not in dir(info.infCad):
                        return
                    cep = get_value(info.infCad.ender, 'CEP') or ''
                    self.zip = misc.format_zipcode(str(cep).zfill(8) if cep else '', self.country_id.code)
                    self.street_name = get_value(info.infCad.ender, 'xLgr')
                    self.street_number = get_value(info.infCad.ender, 'nro')
                    self.street2 = get_value(info.infCad.ender, 'xCpl')
                    self.district = get_value(info.infCad.ender, 'xBairro')
                    cMun = get_value(info.infCad.ender, 'cMun')
                    xMun = get_value(info.infCad.ender, 'xMun')
                    city = None
                    if cMun:
                        city = self.env['res.city'].search([('ibge_code', '=', str(cMun)),('state_id', '=', self.state_id.id)])
                    if not city and xMun:
                        city = self.env['res.city'].search([('name', 'ilike', xMun),('state_id', '=', self.state_id.id)])
                    if city:
                        self.city_id = city.id
                    # self.onchange_inscr_est()
                else:
                    msg = "%s - %s" % (info.cStat, info.xMotivo)
                    raise UserError(msg)
            else:
                raise UserError(resposta['received_xml'])
        else:
            raise UserError(_('Fill the State and CNPJ fields to search'))
        return True
