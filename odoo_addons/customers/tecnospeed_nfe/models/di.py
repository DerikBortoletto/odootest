

from odoo import api, fields, models, _, exceptions
import re


class DI(models.Model):
    _inherit = 'purchase.order'

    
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



    is_importa = fields.Boolean('É uma importação ?')

    
       
       

        


    
    nDI = fields.Char('Número do DI', help="Numero do Documento de Importação", size = 10)

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

   
    @api.model
    def create(self, vals):
        # self.check_ndi_size(vals)
        return super(DI, self).create(vals)

    def write(self, vals):
        # self.check_ndi_size(vals)
        res = super(DI, self).write(vals)
        return res

