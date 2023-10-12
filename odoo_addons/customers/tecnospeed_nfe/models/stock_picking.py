from odoo import fields, models, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'


    transporte_ids = fields.Many2many(
    comodel_name='tecnospeed.transporte'
    )