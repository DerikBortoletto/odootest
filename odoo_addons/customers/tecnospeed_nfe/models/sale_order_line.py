from odoo import fields, models, api, _


## Plug notas DOC : https://docs.plugnotas.com.br/#tag/NFe/operation/addNFe please refer to that documentation if you have any questions about the fields listed in the model below.
## Model created for itens used in Sales Order Line using the plugnotas documentation as reference. 


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    itens_valorFrete = fields.Float('Valor Total do Frete')
    itens_valorSeguro = fields.Float('Valor Total do Seguro')
    itens_valorOutros = fields.Float('Outras Despesas')
    valor_unitario_comerc = fields.Float('Valor Unitário Comercial')
    valor_unitario_tribut = fields.Float('Valor Unitário Tributável')