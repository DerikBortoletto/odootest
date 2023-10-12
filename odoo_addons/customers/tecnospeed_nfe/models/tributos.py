import re
from datetime import datetime, date

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

## Plug notas DOC : https://docs.plugnotas.com.br/#tag/NFe/operation/addNFe please refer to that documentation if you have any questions about the fields listed in the model below.
## Model created for tax tributes using the plugnotas documentation as reference. itens -> tributos


class Tributos(models.Model):

    _inherit = 'purchase.order.line'
   
    ORIGEM = [
    
   ( '0',    "0 - Nacional, exceto as indicadas nos códigos 3, 4, 5 e 8"),
   ( '1',    "1 - Estrangeira - Importação direta, exceto a indicada no código 6"),
   ( '2',    "2 - Estrangeira - Adquirida no mercado interno, exceto a indicada no código 7"),
   ( '3',    "3 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 40% e inferior ou igual a 70%"),
   ( '4',    "4 - Nacional, cuja produção tenha sido feita em conformidade com os processos produtivos básicos de que tratam as legislações citadas nos Ajustes"),
   ( '5',    "5 - Nacional, mercadoria ou bem com Conteúdo de Importação inferior ou igual a 40%"),
   ( '6',    "6 - Estrangeira - Importação direta, sem similar nacional, constante em lista da CAMEX e gás natural"),
   ( '7',    "7 - Estrangeira - Adquirida no mercado interno, sem similar nacional, constante lista CAMEX e gás natural."),
   ( '8',    "8 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 70%"), 
]

    MODALIDADEDETERMINACAO = [    
        ('0',   "0 - Margem Valor Agregado (%)"),
        ('1',   "1 - Pauta (Valor)"),
        ('2',   "2 - Preço Tabelado Máx. (valor)"),
        ('3',   "3 - Valor da operação"),
    ]

    CST_ENTRADA = [    
        ('00',   "00 - Entrada com recuperação de crédito"),
        ('01',   "01 - Entrada tributada com aliquota zero"),
        ('02',   "02 - Entrada isenta"),
        ('03',   "03 - Entrada não-tributada"),
        ('04',   "04 - Entrada imune"),
        ('05',   "05 - Entrada com suspensão"),
    ]

    CST_SAIDA = [    
        ('49',   "49 - Outras entradas"),
        ('50',   "50 - Saída tributada"),
        ('51',   "51 - Saída tributada com alíquota zero"),
        ('52',   "52 - Saída isenta"),
        ('53',   "53 - Saída não-tributada"),
        ('54',   "54 - Saída imune"),
        ('55',   "55 - Saída com suspensão"),
        ('99',   "99 - Outras saídas"),
    ]

    COD_EXIGIBILIDADE = [    
        ('1',   "1 - Exigível"),
        ('2',   "2 - Saída tributada"),
        ('3',   "3 - Saída tributada com alíquota zero"),
        ('4',   "4 - Saída isenta"),
        ('5',   "5 - Saída não-tributada"),
        ('6',   "6 - Saída imune"),
        ('7',   "7 - Saída com suspensão"),
        
    ]

    PIS_CST =[    

        ("01", "01 - Operação Tributável (base de cálculo = valor da operação alíquota normal (cumulativo/não cumulativo));"),
        ("02", "02 - Operação Tributável (base de cálculo = valor da operação (alíquota diferenciada));"),
        ("03", "03 - Operação Tributável (base de cálculo = quantidade vendida x alíquota por unidade de produto);"),
        ("04", "04 - Operação Tributável (tributação monofásica (alíquota zero));"),
        ("05", "05 - Operação Tributável (Substituição Tributária);"),
        ("06", "06 - Operação Tributável (alíquota zero);"),
        ("07", "07 - Operação Isenta da Contribuição;"),
        ("08", "08 - Operação Sem Incidência da Contribuição;"),
        ("09", "09 - Operação com Suspensão da Contribuição;"),
        ("49", "49 - Outras Operações de Saída;"),
        ("50", "50 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Tributada no Mercado Interno;"),
        ("51", "51 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Não Tributada no Mercado Interno;"),
        ("52", "52 - Operação com Direito a Crédito – Vinculada Exclusivamente a Receita de Exportação;"),
        ("53", "53 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno;"),
        ("54", "54 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas no Mercado Interno e de Exportação;"),
        ("55", "55 - Operação com Direito a Crédito - Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação;"),
        ("56", "56 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno, e de Exportação;"),
        ("60", "60 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Tributada no Mercado Interno;"),
        ("61", "61 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Não-Tributada no Mercado Interno;"),
        ("62", "62 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita de Exportação;"),
        ("63", "63 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno;"),
        ("64", "64 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas no Mercado Interno e de Exportação;"),
        ("65", "65 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação;"),
        ("66", "66 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno, e de Exportação;"),
        ("67", "67 - Crédito Presumido - Outras Operações;"),
        ("70", "70 - Operação de Aquisição sem Direito a Crédito;"),
        ("71", "71 - Operação de Aquisição com Isenção;"),
        ("72", "72 - Operação de Aquisição com Suspensão;"),
        ("73", "73 - Operação de Aquisição a Alíquota Zero;"),
        ("74", "74 - Operação de Aquisição; sem Incidência da Contribuição;"),
        ("75", "75 - Operação de Aquisição por Substituição Tributária;"),
        ("98", "98 - Outras Operações de Entrada;"),
        ("99", "99 - Outras Operações;"),

]

    #is_importa mesmo field utilizado no purchase.order, utilizado apenas para esconder a página Imposto de Importação na view order_line
    is_importa = fields.Boolean('É importação ?')
  
    


        

    #CFOP 

    cfop = fields.Char('CFOP')


    #Valor Total Bruto dos Produtos ou Serviços
    valor_total_bruto = fields.Float('Valor Total Bruto Produtos Ou Serviços')

    #tags inside ICMS tag
     
    icms_origem = fields.Selection(
        ORIGEM,
        string = 'Origem da Mercadoria',

    )
  

    icms_cst = fields.Char('Cód. ST', size = 3, help = 'Código de Situação Tributária')
    icms_aliquota = fields.Float('Aliq Imposto', digits = (3,4))
    icms_valor = fields.Float('Valor ICMS', digits = (13,2), help = ' Valor do ICMS')

    #Fields inside ICMS tag -> Base Calculo
    icms_BC_modalidadeDeterminacao = fields.Selection(
        MODALIDADEDETERMINACAO,
        string = 'Mod. Det. BC do ICMS',
        help = 'Modalidade Determinação da BC do ICMS'
    )
    icms_BC_valor = fields.Float('Valor Base Calculo', digits =(13,2))

    #Fields inside ICMS tag -> Substituicao Tributaria
    icms_ST_aliq = fields.Float('Aliquota do imposto ICMS ST', digits = (3,4))
    icms_ST_valor = fields.Float('Valor da BC ICMS ST', digits=(13,2))
    icms_ST_percentualReducao = fields.Float('% redução BC ICMS ST', digits = (3,4), help = 'Percentual da Redução de BC do ICMS ST')
    icms_ST_margemValorAdicionado_percent = fields.Float('% margem valor adic ICMS ST', digits =(3,4), help = 'Percentual de Margem de valor adicionado ao ICMS ST')
    icms_ST_FCP_aliq = fields.Float('Aliquota FCP', digits = (3,4), help = 'Percentual relativo ao Fundo de Combate à Pobreza (FCP)')
    icms_ST_FCP_BC_valor = fields.Float('Valor da Base de Cálculo do FCP', digits = (13,2), help = ' Valor da Base de Cálculo do FCP')
    icms_ST_valor = fields.Float('Valor ICMS FCP', digits = (13,2), help = ' Valor do ICMS relativo ao Fundo de Combate à pobreza (FCP)')



    ##IPI fields 

    ipi_cnpjProdutor = fields.Char('CNPJ do produtor', size = 14, help = 'CNPJ do produtor da mercadoria, quando diferente do emitente. Somente para os casos de exportação direta ou indireta')
    ipi_seloControle_code = fields.Char('Código selo controle IPI', size = 60, help = 'Código do selo de controle IPI')
    ipi_seloControle_quantidade = fields.Integer('Quantidade selo de controle', size =12)

    #IPI -> codigoEnquadramentoLegal
    ipi_codEnquadramento = fields.Char('Código Enquadramento Legal IPI', size =2)

    #IPI - > CST
    ipi_cst_entrada = fields.Selection(
            CST_ENTRADA,
            string = 'IPI Entrada',
            )

    ipi_cst_saida = fields.Selection(
        CST_SAIDA,
        string = 'IPI Saída',
        )

    #Fields used only when the variable ipi_cst_saida = 49,50,99 or ipi_cst_entrada = 00, conditions are inside attrs in tributos.xml
    ipi_baseCalculo = fields.Float('Valor BC IPI')
    ipi_aliquota = fields.Float('Aliquota do IPI')
    ipi_valor = fields.Float('Valor do IPI')

    #IPI -> unidade

    ipi_unidade_qty = fields.Integer('Quantidade total unidade p/tributação')
    ipi_unidade_valor = fields.Float('Valor por Unidade Tributavel')


    #PIS

    pis_cst = fields.Selection(
        PIS_CST,
        string = 'CST do PIS'
    )

    pis_aliq = fields.Float('Aliquota do PIS (%)')
    pis_valor = fields.Float('Valor do PIS')
    

    #PIS -> baseCalculo

    pis_BC_valor = fields.Float('Valor da base de calculo PIS')
    pis_BC_quantidade = fields.Float('Quantidade BC')


    #PIS -> substituicaoTributaria

    pis_ST_BC = fields.Float('Base Calculo Substituicao Tributaria PIS')
    pis_ST_aliquota = fields.Float('Aliquota Substituicao Tributaria PIS')
    pis_ST_valor = fields.Float('Valor Substituicao Tributaria PIS')


    #TODO: Verificar com a tecnospeed sobre o campo quantidadeVendida dentro do PIS e  Substituicao Tributaria do PIS


    ##COFINS 

    cofins_cst = fields.Char('Código Situação Tributária COFINS')
    cofins_aliq = fields.Float('Aliquota COFINS')
    cofins_valor = fields.Float('Valor COFINS')

    #COFINS -> baseCalculo

    cofins_BC_valor = fields.Float('Valor Base de Calculo COFINS')

    #COFINS -> substituicaoTributaria

    cofins_ST_BC = fields.Float('Base de calculo ST COFINS')
    cofins_ST_aliquota = fields.Float('Aliquota ST COFINS')
    cofins_ST_valor = fields.Float('Valor ST COFINS')

    #ISSQN 

    issqn_valor = fields.Float('Valor do ISSQN')
    issqn_aliquota = fields.Float('Aliquota do ISSQN')
    issqn_baseCalculo = fields.Float('Base de calculo do ISSQN')
    issqn_codigoServico = fields.Char('Código do Serviço')
    issqn_valorDeducao = fields.Char('Valor deducao para redução da Base de Calculo')
    issqn_valorOutros = fields.Float('Valor outras retenções')
    issqn_descontoIncondicionado = fields.Float('Valor desconto Incondicionado')
    issqn_descontoCondicionado = fields.Float('Valor desconto Condicionado')
    issqn_valorRetencaoIss = fields.Float('Valor retencao ISS')
    issqn_codMunicipalServico = fields.Float('Código Municipal do Serviço')
    issqn_codMunicipioIncidencia = fields.Char('Código Municipal Incidencia Imposto')
    issqn_codMunicipioFatoGerador = fields.Char('Código Municipio fato Gerador ISSQN')
    issqn_codigoExigibilidade = fields.Selection(
        COD_EXIGIBILIDADE,
        string = "Código Exigibilidade"
    )

    # Imposto de Importação 

    II_BC = fields.Float('Valor BC do II')
    II_vDA = fields.Float('Valor despesas aduaneiras')
    II_valor = fields.Float('Valor do II')
    II_vOP = fields.Float('Valor Imposto Sobre Operações Financeiras')
    

    
    
    




