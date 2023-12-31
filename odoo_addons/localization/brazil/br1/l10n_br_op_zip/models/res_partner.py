
import re
from odoo import models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('zip')
    def _onchange_zip(self):
        cep = re.sub('[^0-9]', '', self.zip or '')
        if len(cep) == 8:
            return self.zip_search(cep)

    def zip_search(self, cep):
        self.zip = "%s-%s" % (cep[0:5], cep[5:8])
        res = self.env['br.zip'].search_by_zip(zip_code=self.zip)
        if res:
            self.update(res)
        else:
            return {
                'warning': {
                    'title': 'Pesquisa de CEP',
                    'message': 'Nenhum CEP encontrado!',
                }
            }

    @api.onchange('street', 'city_id', 'district')
    def _search_street(self):
        if self.street and self.city_id and not self.zip:
            res = self.env['br.zip'].search_by_address(
                country_id=self.city_id.state_id.country_id.id,
                state_id=self.city_id.state_id.id,
                city_id=self.city_id.id,
                street=self.street,
                obj=None,
                district=self.district,
                error=False
            )
            if res:
                self.update(res)
