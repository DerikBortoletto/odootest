from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import datetime

class StockPicking(models.Model):
    _inherit = 'stock.production.lot'


    manufacture_date = fields.Date('Manufacture Date')

    @api.constrains('manufacture_date')
    def _check_data(self):
        for record in self:
            if record.manufacture_date and record.manufacture_date > datetime.datetime.now().date():
                raise ValidationError("A data de fabricação não pode ser maior que a data de hoje")
