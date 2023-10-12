
from odoo import api, fields, models, tools, _

class Currency(models.Model):
    _inherit = "res.currency"

    #TODO: Verificar
    # @api.model
    # def _get_conversion_rate(self, from_currency, to_currency):
    #     # Ajuste na conversão da moeda, o original o Odoo converte da moeda secundária para a principal
    #     from_currency = from_currency.with_env(self.env)
    #     to_currency = to_currency.with_env(self.env)
    #     return  from_currency.rate / to_currency.rate
