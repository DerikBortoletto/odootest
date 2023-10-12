from odoo import fields, models, api, _

class Transporte(models.Model):
    _name = "tecnospeed.transporte"
    _rec_name = "transp_nome"

    MODALIDEFRETE = [
        ("0",  "0 - Por conta do emitente"),
        ("1",  "1 - Por conta do destinatário/remetente"),
        ("2",  "2 - Por conta de terceiros"),
        ("3",  "3 - Transporte Próprio por conta do Remetente"),
        ("4",  "4 - Transporte Próprio por conta do Destinatário"),
        ("9",  "9 - Sem frete"),
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

    modalidadeFrete = fields.Selection(
        MODALIDEFRETE,
        string = "Modalidade do Frete"
    )

    veiculo_placa = fields.Char('Placa do Veículo')
    veiculo_uf = fields.Selection(
        TUFEMI_2,
        string = 'UF'
    )
    veiculo_rntc = fields.Char('ANTT', help = "Registro Nacional de Transportador de Carga (ANTT)")


    ##Dados do Transportador

    transp_cnpj = fields.Char('CNPJ', size = 14)
    transp_cpf = fields.Char('CPF', size = 11)
    transp_nome = fields.Char('Razão social ou nome do Transportador')
    transp_logradouro = fields.Char('Endereço Completo')
    transp_descricaoCidade = fields.Char('Municipio')
    transp_endereco_uf = fields.Selection(
        TUFEMI,
        string = "Sigla da UF"

    )

    




