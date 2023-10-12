import re
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from .cst import CST_ICMS,CST_IPI

class CFOP(models.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _name = 'br.cfop'
    _description = 'CFOP'

    code = fields.Char('Código', size=4, required=True)
    name = fields.Char('Nome', size=256, required=True)
    small_name = fields.Char('Nome Reduzido', size=32, required=True)
    description = fields.Text('Descrição')
    type = fields.Selection([('input', 'Entrada'),('output', 'Saída')],'Tipo', required=True)
    parent_id = fields.Many2one('br.cfop', 'CFOP Pai')
    child_ids = fields.One2many('br.cfop', 'parent_id', 'CFOP Filhos')
    internal_type = fields.Selection([('view', 'Visualização'), ('normal', 'Normal')], 'Tipo Interno', 
                                     required=True, default='normal')

    _sql_constraints = [('cfop_code_uniq', 'unique (code)', 'Já existe um CFOP com esse código !')]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result

class ServiceType(models.Model):
    _name = 'br.service.type'
    _description = 'Cadastro de Operações Fiscais de Serviço'

    code = fields.Char('Código', size=16, required=True)
    name = fields.Char('Descrição', size=256, required=True)
    parent_id = fields.Many2one('br.service.type', 'Tipo de Serviço Pai')
    child_ids = fields.One2many('br.service.type', 'parent_id', 'Tipo de Serviço Filhos')
    internal_type = fields.Selection([('view', 'Visualização'), ('normal', 'Normal')], 'Tipo Interno', required=True, default='normal')
    federal_nacional = fields.Float('Imposto Fed. Sobre Serviço Nacional',company_dependent=True)
    federal_importado = fields.Float('Imposto Fed. Sobre Serviço Importado',company_dependent=True)
    estadual_imposto = fields.Float('Imposto Estadual',company_dependent=True)
    municipal_imposto = fields.Float('Imposto Municipal',company_dependent=True)
    sincronizado_ibpt = fields.Boolean(default=False)
    fonte_impostos = fields.Char(string="Fonte dos Impostos", size=100)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result

class NCM(models.Model):
    _name = 'br.ncm'
    _description = 'Classificações Fiscais (NCM) - Nomenclatura Comum do Mercosul'

    code = fields.Char(string="Código", size=14)
    category = fields.Char(string="Categoria", size=14)
    name = fields.Char(string="Nome", size=300)
    company_id = fields.Many2one('res.company', string="Empresa")
    unidade_tributacao = fields.Char(string="Unidade Tributável", size=4)
    descricao_unidade = fields.Char(string="Descrição Unidade", size=20)
    federal_nacional = fields.Float('Imposto Fed. Sobre Produto Nacional')
    federal_importado = fields.Float('Imposto Fed. Sobre Produto Importado')
    estadual_imposto = fields.Float('Imposto Estadual')
    municipal_imposto = fields.Float('Imposto Municipal')
    sincronizado_ibpt = fields.Boolean(default=False)
    fonte_impostos = fields.Char(string="Fonte dos Impostos", size=100)

    # IPI
    classe_enquadramento_id = fields.Many2one('br.enquadramento.ipi', string="Classe Enquadr.")
    # CEST
    cest_id = fields.Many2one('br.cest', string="CEST")
    
    active = fields.Boolean(default=True, string='Ativo')

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result

    def notify_account_users(self, message):
        group_id = self.env.ref("base.group_system").id
        users = self.env['res.users'].search([('groups_id', '=', group_id)])
        for user in users:
            partner = user.partner_id

            odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")

            channel_info = self.env['mail.channel'].channel_get([partner.id, odoobot_id], pin=True)
            channel = self.env['mail.channel'].browse(channel_info['id'])
            channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment", subtype="mail.mt_comment")

    def cron_sync_average_tax_rate(self):
        if not self.env.company.l10n_br_ibpt_api_token:
            message = "Você ainda não configurou o sistema para a lei de Olho no Imposto. " + \
                "Crie um token aqui: https://deolhonoimposto.ibpt.org.br/Site/PassoPasso " + \
                "E depois registre o mesmo em configurações da empresa. Após isto o sistema irá "+ \
                "sincronizar automaticamente as informações."
            self.notify_account_users(message)
            return

        headers = {
            "content-type": "application/json;",
        }

        products = self.env['product.template'].search([('l10n_br_ncm_id.sincronizado_ibpt', '=', False)])

        for ncm in products.mapped('l10n_br_ncm_id'):
            url = 'https://apidoni.ibpt.org.br/api/v1/produtos'
            data = {
                'token': self.env.company.l10n_br_ibpt_api_token,
                'cnpj': re.sub('[^0-9]', '', self.env.company.l10n_br_cnpj_cpf or ''),
                'codigo': re.sub('[^0-9]', '', ncm.code or ''),
                'uf': self.env.company.state_id.code,
                'ex': 0,
                'descricao': '-----',
                'unidadeMedida': ncm.unidade_tributacao,
                'valor': 1,
                'gtin': '-',
            }
            response = requests.get(url, params=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            ncm.write({
                'federal_nacional': result['Nacional'],
                'federal_importado': result['Importado'],
                'estadual_imposto': result['Estadual'],
                'municipal_imposto': result['Municipal'],
                'fonte_impostos': result['Fonte'],
                'sincronizado_ibpt': True,
            })
            self.env.cr.commit()

        services = self.env['product.template'].search([('service_type_id.sincronizado_ibpt', '=', False)])

        for ncm in services.mapped('service_type_id'):
            url = 'https://apidoni.ibpt.org.br/api/v1/servicos'
            data = {
                'token': self.env.company.l10n_br_ibpt_api_token,
                'cnpj': re.sub('[^0-9]', '', self.env.company.l10n_br_cnpj_cpf or ''),
                'codigo': re.sub('[^0-9]', '', ncm.code or ''),
                'uf': self.env.company.state_id.code,
                'descricao': '-----',
                'unidadeMedida': 'UN',
                'valor': 1,
            }
            response = requests.get(url, params=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            ncm.write({
                'federal_nacional': result['Nacional'],
                'federal_importado': result['Importado'],
                'estadual_imposto': result['Estadual'],
                'municipal_imposto': result['Municipal'],
                'fonte_impostos': result['Fonte'],
                'sincronizado_ibpt': True,
            })
            self.env.cr.commit()

class ProductFiscalCategory(models.Model):
    _name = 'br.product.fiscal.category'
    _description = 'Categoria Fiscal'

    code = fields.Char(string="Código", size=14)
    name = fields.Char('Descrição', required=True)
    company_id = fields.Many2one('res.company', string="Empresa", default=lambda self: self.env.user.company_id)
    active = fields.Boolean(default=True, string='Ativo')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result

class CNAE(models.Model):
    _name = 'br.cnae'
    _description = 'Cadastro de CNAE'

    code = fields.Char('Código', size=16, required=True)
    name = fields.Char('Descrição', size=64, required=True)
    version = fields.Char('Versão', size=16, required=True)
    parent_id = fields.Many2one('br.cnae', 'CNAE Pai')
    child_ids = fields.One2many('br.cnae', 'parent_id', 'CNAEs Filhos')
    internal_type = fields.Selection([('view', 'Visualização'), ('normal', 'Normal')],
                                     'Tipo Interno', required=True, default='normal')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result

class BeneficioFiscal(models.Model):
    _name = 'br.beneficio.fiscal'
    _description = 'Código de Benefício Fiscal'

    code = fields.Char('Código',size=10)
    name = fields.Char('Descrição', required=True)
    state_id = fields.Many2one('res.country.state', 'Estado', domain="[('country_id.code', '=', 'BR')]", required=True)
    dt_start = fields.Date('Data Inicial')
    dt_end = fields.Date('Data Final')
    cst_icms = fields.Char('CSTs do ICMS') #TODO: Fazer relacionado com as CSTs
    memo = fields.Text('Observação')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result

class EnquadramentoIPI(models.Model):
    _name = 'br.enquadramento.ipi'
    _description = """Código de enquadramento do IPI"""
    _order = 'code'

    code = fields.Char('Código',size=3, required=True,index=True)
    name = fields.Char('Descrição', required=True,index=True)
    grupo = fields.Char('Grupo', size=15, required=True,index=True)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result

class TIPI(models.Model):
    _name = 'br.tipi'
    _description = """Tabela de incidência do IPI"""
    _order = 'name, nivel, ncm_id'

    name = fields.Char('Capítulo',size=3, required=True,index=True)
    ncm_id = fields.Many2one('br.ncm', string="NCM", required=True, index=True)
    is_exception = fields.Boolean(string="Exceção")
    nivel = fields.Integer('Nível')
    tax_id = fields.Many2one('account.tax',string='Aliquota')
    dt_start = fields.Date('Data Inicial')
    dt_end = fields.Date('Data Final')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.name, rec.nivel or '')))
        return result

class CEST(models.Model):
    _name = 'br.cest'
    _description = """Código Especificador da Substituição Tributária"""
    _order = 'code'

    code = fields.Char('Código',size=10, required=True,index=True)
    name = fields.Char('Descrição', required=True,index=True)
    segment = fields.Char('Segmento')
    anexo = fields.Char('Anexo',size=5,required=True,index=True)
    ncm_ids = fields.Many2many('br.ncm', 'br_cest_ncm_rel', 'cest_id', 'ncm_id', string="NCMs", copy=False)


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result
