from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    presentation_name = fields.Many2one('product.presentation', string='Presentation')