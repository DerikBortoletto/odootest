from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo





class pharma_dosage_forms(models.Model):
    _name = 'pharma.dosage.forms.spt'
    _inherit = "custom.connector.spt"
    _description = 'List of dosage forms for pharmaceutical products'
    _OdooToTTRx = {'tt_id':'dosage_forms_id'}
    _TTRxToOdoo = {'id': 'tt_id'}
    _order = 'name'
    _TTRxKey = 'tt_id'

    tt_id = fields.Char('TT ID', readonly=True, copy=False)
    created_on = fields.Datetime('Create on', readonly=True, copy=False)
    last_update = fields.Datetime('Last Update', readonly=True, copy=False)
    name = fields.Char("Name")
    code = fields.Char("Code")
    is_internal = fields.Boolean('Is Internal', readonly=True)
    
    def FromOdooToTTRx(self, connector, values={}):
        """ From the odoo fields to the TTr2 fields """
        var = {
            'dosage_forms_id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'code': values.get('code',self.code),
            'name': values.get('name',self.name),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        """ From the TTr2 fields to the Odoo fields """
        var = {
            'tt_id': values.get('id'),
            'created_on': DateTimeToOdoo(values['created_on']),
            'last_update': DateTimeToOdoo(values['last_update']),
            'name': values.get('name'),
            'code': values.get('code'),
            'is_internal': values.get('is_internal'),
        }
        CleanDataDict(var)
        return var

    def action_send(self):
        for reg in self:
            reg.CreateInTTRx()
        return True

    def action_test(self):
        resposta = {'id': '9'}
        res = {}
        for key, value in resposta.items():
            odoo_key = self._TTRxToOdoo.get(key)
            if bool(odoo_key):
                res[odoo_key] = value
        print(str(res))

        return True
