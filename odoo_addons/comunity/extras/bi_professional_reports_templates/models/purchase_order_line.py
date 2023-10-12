from odoo import fields, models, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    presentation_id = fields.Many2one(related='product_id.presentation_name')
    