from odoo import fields, models

class ProductPresentation(models.Model):
    _name = 'product.presentation'
    _description = 'Product Presentation'

    name = fields.Char(string="Presentation Name", required=True)
    observation = fields.Text(string="Observations")