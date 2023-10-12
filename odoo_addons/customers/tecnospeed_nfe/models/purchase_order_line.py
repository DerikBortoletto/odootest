from odoo import fields, models, api, _


## Plug notas DOC : https://docs.plugnotas.com.br/#tag/NFe/operation/addNFe please refer to that documentation if you have any questions about the fields listed in the model below.
## Model created for itens used in Purchase Order Line using the plugnotas documentation as reference. 


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    itens_valorFrete = fields.Float('Valor Total do Frete')
    itens_valorSeguro = fields.Float('Valor Total do Seguro')
    itens_valorOutros = fields.Float('Outras Despesas')
    
    valor_unitario_comerc = fields.Float('Valor Unitário Comercial')
    valor_unitario_tribut = fields.Float('Valor Unitário Tributável')