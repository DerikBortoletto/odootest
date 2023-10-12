import re
import base64
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.l10n_br_op_base.tools.fiscal import IND_IE_DEST, FRT_RESP

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import consulta_cadastro
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    freight_responsibility = fields.Selection(FRT_RESP, 'Modalidade do frete')
    billing_id = fields.Many2one('res.partner', compute='_compute_addresses', string="Cobrança", store=True)
    contact_id = fields.Many2one('res.partner', compute='_compute_addresses', string="Contato", store=True)
    email_nfe = fields.Char(string="E-Mail Doc. Eletr.", help="e-Mail para onde os documentos eletrônicos a receber serão enviados, caso esteja em branco vai para o e-Mail padrão.")

    def action_check_sefaz(self):
        self.ensure_one()
        if self.cnpj_cpf and self.state_id:
            if self.state_id.code == 'AL':
                raise UserError(_('Alagoas doesn\'t have this service'))
            if self.state_id.code == 'RJ':
                raise UserError(_('Rio de Janeiro doesn\'t have this service'))
            company = self.env.user.company_id
            if not company.nfe_a1_file and not company.nfe_a1_password:
                raise UserError(_('Configure the company\'s certificate and password'))
            cert = company.with_context({'bin_size': False}).nfe_a1_file
            cert_pfx = base64.decodestring(cert)
            certificado = Certificado(cert_pfx, company.nfe_a1_password)
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
                    self.zip = str(cep).zfill(8) if cep else ''
                    self.street = get_value(info.infCad.ender, 'xLgr')
                    self.number = get_value(info.infCad.ender, 'nro')
                    self.street2 = get_value(info.infCad.ender, 'xCpl')
                    self.district = get_value(info.infCad.ender, 'xBairro')
                    cMun = get_value(info.infCad.ender, 'cMun')
                    xMun = get_value(info.infCad.ender, 'xMun')
                    city = None
                    if cMun:
                        city = self.env['res.state.city'].search(
                            [('ibge_code', '=', str(cMun)[2:]),
                             ('state_id', '=', self.state_id.id)])
                    if not city and xMun:
                        city = self.env['res.state.city'].search(
                            [('name', 'ilike', xMun),
                             ('state_id', '=', self.state_id.id)])
                    if city:
                        self.city_id = city.id
                    self.onchange_inscr_est()
                else:
                    msg = "%s - %s" % (info.cStat, info.xMotivo)
                    raise UserError(msg)
            else:
                raise UserError(resposta['received_xml'])
        else:
            raise UserError(_('Fill the State and CNPJ fields to search'))
        return True

    #TODO: Verificar
    # def _invoice_total(self):
    #     account_invoice_report = self.env['account.invoice.report']
    #     if not self.ids:
    #         self.total_invoiced = 0.0
    #         return True
    #
    #     # Filter added to filter invoice total with only sales.
    #     # Journal with types: purchase, cash, general and bank
    #     # should not be included when calculating invoice total
    #     journal_ids = self.env['account.journal'].search([('type', '=', 'sale')]).ids
    #
    #     all_partners_and_children = {}
    #     all_partner_ids = []
    #     for partner in self:
    #         # price_total is in the company currency
    #         all_partners_and_children[partner] = self.search([('id', 'child_of', partner.id)]).ids
    #         all_partner_ids += all_partners_and_children[partner]
    #
    #     # searching account.invoice.report via the orm is comparatively
    #     # expensive (generates queries "id in []" forcing
    #     # to build the full table).
    #     # In simple cases where all invoices are in the same currency
    #     # than the user's company access directly these elements
    #
    #     # generate where clause to include multicompany rules
    #     where_query = account_invoice_report._where_calc([
    #         ('partner_id', 'in', all_partner_ids),
    #         ('state', 'not in', ['draft', 'cancel']),
    #         ('company_id', '=', self.env.user.company_id.id),
    #         ('move_type', 'in', ('out_invoice', 'out_refund')),
    #         ('journal_id', 'in', journal_ids)])
    #     account_invoice_report._apply_ir_rules(where_query, 'read')
    #     from_clause, where_clause, where_clause_params = where_query.get_sql()
    #
    #     # price_total is in the company currency
    #     # pylint: disable=E8103
    #     query = """
    #               SELECT SUM(price_total) as total, partner_id
    #                 FROM account_invoice_report account_invoice_report
    #                WHERE %s
    #                GROUP BY partner_id
    #             """ % where_clause
    #     self.env.cr.execute(query, where_clause_params)
    #     price_totals = self.env.cr.dictfetchall()
    #     for partner, child_ids in all_partners_and_children.items():
    #         total = 0.0
    #         for price in price_totals:
    #             if price['partner_id'] in child_ids:
    #                 total += price['total']
    #         partner.total_invoiced = total

    @api.depends('child_ids')
    def _compute_addresses(self):
        """ Procura o endereço de Cobrança e Contato e caso não haja devolve o endereço atual """
        for reg in self:
            # Procura o endereço de cobrança
            billing = self.env['res.partner'].search([('parent_id','=',reg.id),('type','=','invoice')],limit=1)
            contact = self.env['res.partner'].search([('parent_id','=',reg.id),('type','=','contact')],limit=1)
            # Passa o endereco caso tenha
            reg.billing_id = billing
            reg.contact_id = contact

    @api.onchange('inscr_est','company_type')
    def onchange_inscr_est(self):
        if self.company_type == "company":
            if bool(self.inscr_est):
                self.indicador_ie_dest = "1"
            elif self.state_id.code in ['AM','BA','CE','GO','MG','MS','MT','PE','RN','SP']:
                self.indicador_ie_dest = "9"
            else:
                self.indicador_ie_dest = "2"
        else:
            self.indicador_ie_dest = "9"
