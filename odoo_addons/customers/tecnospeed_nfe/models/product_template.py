
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

## Plug notas DOC : https://docs.plugnotas.com.br/#tag/NFe/operation/addNFe please refer to that documentation if you have any questions about the fields listed in the model below.
## Model created for  tributes using the plugnotas documentation as reference. itens TAG


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    ncm = fields.Char('Código NCM', size = 10)
    cest = fields.Char('Código CEST')

    @api.constrains('ncm')
    def ncm_validation(self):
         if len(self.ncm) < 8 or len(self.ncm) == 9:
            raise ValidationError('Tamanho do código NCM incorreto, favor inserir um código de 8 ou 10 caracteres')


    

        
       
            

