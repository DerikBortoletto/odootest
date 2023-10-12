

from odoo import api, fields, models, _, exceptions
import re
from odoo.addons.l10n_br_op_base.tools.fiscal import validate_cnpj

class DI(models.Model):
    _name = "l10n_br_fiscal.di"
    # _inherit = ["nfe.40.di"]
    _rec_name = 'nDI'
    # _inherit = 'spec.mixin.nfe'
    _description = "Declaração de Importação"
    TPINTERMEDIO_DI = [
    ("1", "1 - Importação por conta própria"),
    ("2", "2 - Importação por conta e ordem"),
    ("3", "3 - Importação por encomenda"),
]
    TPVIATRANSP_DI = [
    ("1", "1 - Maritima"),
    ("2", "2 - Fluvial"),
    ("3", "3 - Lacustre"),
    ("4", "4 - Aérea"),
    ("5", "5 - Postal"),
    ("6", "6 - Ferroviária"),
    ("7", "7 - Rodoviária"),
    ("8", "8 - Conduto/Rede Transmissão"),
    ("9", "9 - Meios Próprios"),
    ("10", "10 - Entrada/Saída ficta")
]
    TUFEMI = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AM", "AM"),
    ("AP", "AP"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MG", "MG"),
    ("MS", "MS"),
    ("MT", "MT"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("PR", "PR"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("RS", "RS"),
    ("SC", "SC"),
    ("SE", "SE"),
    ("SP", "SP"),
    ("TO", "TO"),
]
    TUFEMI_2 = [

        ("AC", "AC"),
        ("AL", "AL"),
        ("AM", "AM"),
        ("AP", "AP"),
        ("BA", "BA"),
        ("CE", "CE"),
        ("DF", "DF"),
        ("ES", "ES"),
        ("GO", "GO"),
        ("MA", "MA"),
        ("MG", "MG"),
        ("MS", "MS"),
        ("MT", "MT"),
        ("PA", "PA"),
        ("PB", "PB"),
        ("PE", "PE"),
        ("PI", "PI"),
        ("PR", "PR"),
        ("RJ", "RJ"),
        ("RN", "RN"),
        ("RO", "RO"),
        ("RR", "RR"),
        ("RS", "RS"),
        ("SC", "SC"),
        ("SE", "SE"),
        ("SP", "SP"),
        ("TO", "TO"),
    ]



    
    
    nDI = fields.Char('Número do DI', help="Numero do Documento de Importação", size = 10, required =True)

    dDI =  fields.Date(
        string="Data de registro da DI",
        help="Data de registro da DI (AAAA-MM-DD)")

    xLocDesemb = fields.Char(
        string="Local do Desembaraço", size = 60)

    UFDesemb = fields.Selection(
        TUFEMI,
        string="UF Desembaraço",
       )

    UFTerceiro = fields.Selection(
        TUFEMI_2,
        string="UF Terceiro",
    )
    tpViaTransp  = fields.Selection(
        TPVIATRANSP_DI,
        string="Modal de Transporte")

    tpIntermedio = fields.Selection(
        TPINTERMEDIO_DI,
        string="Intermedio")

    dDesemb = fields.Date(
        string="Data do desembaraço aduaneiro",
        help="Data do desembaraço aduaneiro (AAAA-MM-DD)")

    cExportador = fields.Char(
        string="Código do exportador",
        help="Código do exportador (usado nos sistemas internos de"
        "\ninformação do emitente da NF-e)")

    nAdicao = fields.Char(
        string="Número da Adição")
    nSeqAdic = fields.Char(
        string="Número seqüencial do item dentro da Adição")

    # cFabricante = fields.Char(
    #     string="Código do fabricante estrangeiro")

    nfe40_CNPJ = fields.Char(
        string="CNPJ do adquirente ou do encomendante",
       )

    name_intermed = fields.Char(
        string = "Nome do Intermediador"
    )

    # nfe40_vDescDI = fields.Monetary(
    #     currency_field="brl_currency_id",
    #     string="Valor do desconto do item da DI – adição",
    #    )


    @api.onchange('nfe40_CNPJ')
    def check_and_cnpj(self):
        if self.nfe40_CNPJ != False:
            if re.sub('[^0-9]', '', self.nfe40_CNPJ) != "00000000000000" and not validate_cnpj(self.nfe40_CNPJ):
                raise exceptions.ValidationError(_('Invalid CNPJ Number!'))
            else:
                cnpj = re.sub('[^0-9]', '', self.nfe40_CNPJ)
                count = 0
                text = ''
                for i in cnpj:
                    text += i
                    if count == 1:
                        text += '.'
                    if count == 4:
                        text += '.'
                    if count == 7:
                        text += '/'
                    if count == 11:
                        text += '-'
                    count += 1
                    self.nfe40_CNPJ = text




    def check_cnpj(self, vals):
        if re.sub('[^0-9]', '', vals) != "00000000000000" and not validate_cnpj(vals):
            raise exceptions.ValidationError(_('Invalid CNPJ Number!'))
        else:
            cnpj = re.sub('[^0-9]', '', vals)
            count = 0
            text = ''
            for i in cnpj:
                text += i
                if count == 1:
                    text += '.'
                if count == 4:
                    text += '.'
                if count == 7:
                    text += '/'
                if count == 11:
                    text += '-'
                count += 1
            return text
    


    def check_ndi_size(self, vals):
        if vals.get('tpIntermedio'):
            if vals['tpIntermedio'] != '1':
                if vals.get('name_intermed') and vals.get('nfe40_CNPJ'):
                    self.check_cnpj(vals['nfe40_CNPJ'])
                else:
                    raise exceptions.ValidationError('Preencha os campos CNPJ e Nome do Intermediador')

        if vals.get('nDI'):
            numeros = re.findall(r'\d+', vals['nDI'])
            if len(vals['nDI']) < 10:
                raise exceptions.ValidationError('O numero da DI deve conter pelo menos 10 caracteres')
            if str(numeros[0]) != vals['nDI']:
                raise exceptions.ValidationError('O numero da DI deve conter apenas números')


   

    @api.model
    def create(self, vals):
        self.check_ndi_size(vals)
        return super(DI, self).create(vals)

    def write(self, vals):
        self.check_ndi_size(vals)
        res = super(DI, self).write(vals)
        return res


# class is_import_(models.Model):
#     _name = 'l10n_br_fiscal.import'
#     _rec_name = ''
#     _description = "É importacao?"
    
#     is_import = fields.Boolean(string = 'É importação')




#     @api.model
#     def create(self, vals):
#         return super(is_import_, self).create(vals)
    
#     def write(self, vals):
#         res = super(is_import_, self).write(vals)
#         return res