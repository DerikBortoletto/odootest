from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo





class pack_size_type_spt(models.Model):
    _name = 'pack.size.type.spt'
    _inherit = "custom.connector.spt"
    _description = 'Product Pack Size Type'
    _OdooToTTRx = {'tt_id':'packing_type_id'}
    _TTRxToOdoo = {'tt_id':'id'}
    _order = 'name'
    _TTRxKey = 'tt_id'

    tt_id = fields.Char('TT ID')
    created_on = fields.Datetime('Created on')
    last_update = fields.Datetime('Last Update')
    name = fields.Char("Name")
    code = fields.Char("Code")
    is_internal = fields.Boolean('Is Internal')
    
    def FromOdooToTTRx(self, values={}):
        """ From the odoo fields to the TTr2 fields """
        var = {
            'packaging_type_id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'name': values.get('name',self.name),
            'code': values.get('code',self.code),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
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

    def action_refresh(self):
        for reg in self:
            reg.SyncFromTTRx(self.connector_id,myown=True)
        return True

    def action_test(self):
        # 'location': {'location_uuid': 'location_uuid', 'tt_id': 'id'}
        self.SyncFromTTRx(self.connector_id)
        return True
