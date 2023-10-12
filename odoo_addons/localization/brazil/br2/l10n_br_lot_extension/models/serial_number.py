from odoo import api, fields, models


class Product_Serial_Number(models.Model):
     _inherit = 'l10n_br_fiscal.document.line'
     numero_de_serie = fields.Char(string = 'Número de Série')
     