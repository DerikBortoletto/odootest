from odoo import api, fields, models
from .cst import ORIGEM_PROD

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    origin = fields.Selection(ORIGEM_PROD, 'Origem', default='0', company_dependent=True, copy=False)
    ncm_id = fields.Many2one('br.ncm', string="Classificação Fiscal (NCM)")
    cest_id = fields.Many2one('br.cest', string="CEST", help="Código Especificador da Substituição Tributária")

    service_type_id = fields.Many2one('br.service.type', 'Tipo de Serviço')
    service_code = fields.Char(string='Código no Município', company_dependent=True)

    fiscal_category_id = fields.Many2one('br.product.fiscal.category', string='Categoria Fiscal', company_dependent=True)
    tipi_id = fields.Many2one('br.tipi', string='Incidência IPI', domain=[('is_exception','=',False)], company_dependent=True)
    extipi_id = fields.Many2one('br.tipi', string='Exceção IPI', domain=[('is_exception','=',True)], company_dependent=True)
    benef_fiscal_id = fields.Many2one('br.beneficio.fiscal',string="Benefício Fiscal", company_dependent=True)

