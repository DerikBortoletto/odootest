from odoo import fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    presentation_name = fields.Many2one('product.presentation', string='Presentation')