from odoo import fields, models

class StockProductionLotExtension(models.Model):
    _inherit = 'stock.production.lot'

    manufacture_date = fields.Datetime(string='Manufacture Date')