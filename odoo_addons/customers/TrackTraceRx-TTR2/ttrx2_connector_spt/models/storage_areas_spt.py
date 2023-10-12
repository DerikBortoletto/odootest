import logging

from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo

_logger = logging.getLogger(__name__)





class storage_areas_spt(models.Model):
    _name = "storage.areas.spt"
    _inherit = "custom.connector.spt"
    _description = "Storage Areas"
    _inherits = {'stock.location': 'stock_location_id'}
    _TTRxKey = "uuid"
    _OdooToTTRx = {'location_uuid': 'location_uuid', 'uuid': 'uuid'}
    _TTRxToOdoo = {'uuid': 'uuid'}
    

    stock_location_id = fields.Many2one('stock.location', 'Location', auto_join=True, index=True, ondelete="cascade", required=True)
    
    uuid = fields.Char('UUID', copy=False)
    created_on = fields.Datetime('Create On')
    last_update = fields.Datetime('Last Update')
    code = fields.Char("Code")
    gs1_id = fields.Char("GS1 ID")

    cold = fields.Boolean('Cold')
    frozen = fields.Boolean('Frozen')
    high_security = fields.Boolean('High Security / Restricted Access')
    
    notes = fields.Text("Notes")
    is_storage_conditions_verification_disabled = fields.Boolean('Disable Products Storage Condition Verifications')
    
    location_uuid = fields.Char(compute="_compute_location_uuid", store=False)

    @api.depends('location_id')
    def _compute_location_uuid(self):
        for reg in self:
            reg.location_uuid = reg.location_id.location_spt_id.uuid
    
    def FromOdooToTTRx(self, connector, values={}):
        var = super().FromOdooToTTRx(connector=connector,values=values)
        properties = []
        properties += ['COLD'] if bool(values.get('cold',self.cold)) else []
        properties += ['FROZEN'] if bool(values.get('frozen',self.frozen)) else []
        properties += ['RESTRICTED_ACCESS'] if bool(values.get('high_security',self.high_security)) else []
        if bool(values):
            location_uuid = None
            parent_area_uuid = None
            if bool(values.get('location_id')):
                location_id = self.env['stock.location'].browse(values['location_id'])
                location_uuid = location_id.location_spt_id.uuid
                parent_area_uuid = location_id.storage_area_spt_id.uuid
        else:
            parent_area_uuid = self.location_id.storage_area_spt_id.uuid
            location_uuid = self.location_id.location_spt_id.uuid

        var.update({
            'uuid': location_uuid,
            'name': values.get('name',self.name),
            'code': values.get('code',self.code or None if not bool(values) else None),
            'gs1_id': values.get('gs1_id',self.gs1_id or None if not bool(values) else None),
            'parent_area_uuid': parent_area_uuid if bool(parent_area_uuid) else None, 
            'properties': ';'.join(properties),
            'is_active': values.get('active',self.active),
            'notes': values.get('notes',(self.notes or None) if not bool(values) else None),
            'is_storage_conditions_verification_disabled': values.get('is_storage_conditions_verification_disabled',
                                                                      self.is_storage_conditions_verification_disabled),
        })
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        var = super().FromTTRxToOdoo(connector=connector,values=values)
       
        location_id = None        
        if bool(values.get('parent_area_uuid',False)):
            location_id = self.env['storage.areas.spt'].search([('uuid','=',values['parent_area_uuid'])], limit=1).stock_location_id.id
        elif bool(values.get('location_uuid',False)):
            location_id = self.env['locations.management.spt'].search([('uuid','=',values['location_uuid'])], limit=1).stock_location_id.id
        
        var.update({
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': values.get('name'),
            'code': values.get('code'),
            'gs1_id': values.get('gs1_id'),
            'notes': values.get('notes'),
            'is_storage_conditions_verification_disabled': values.get('is_storage_conditions_verification_disabled'),
            'active': values.get('is_active'),
            'location_uuid': values.get('location_uuid'),
            'location_id': location_id,
            'location_type': 'storage',
        })
        if values.get('properties',None) != None:
            properties = values.get('properties',[])
            var['cold'] = True if properties.count('COLD') > 0 else False
            var['frozen'] = True if properties.count('FROZEN') > 0 else False
            var['high_security'] = True if properties.count('RESTRICTED_ACCESS') > 0 else False
        CleanDataDict(var)
        return var

    def AfterCreateFromTTRx(self, connector, response, data):
        self.env['shelf.spt'].SyncFromTTRx(connector, location_uuid=self.location_uuid, storage_uuid=self.uuid)
        return True

    def DeleteInTTRx(self, **params):
        res = super().DeleteInTTRx(**params)
        if (not bool(res) or not bool(res.get('erro'))) and bool(self.stock_location_id):
            self.stock_location_id.unlink()
        return res
            
    def action_send(self):
        for reg in self:
            reg.CreateInTTRx()
        return True

    def action_test(self):
        print(str(self.FromOdooToTTRx(connector=self.connector_id)))
        print(str(self.FromTTRxToOdoo(connector=self.connector_id,
                                      values={'location_uuid': '876b391c-c4a0-11ec-a4da-e091533ef0ea', 
                                       'name': 'storage area teste teste', 'code': 'False', 
                                       'gs1_id': 'False', 
                                       'parent_area_uuid': '6e71d410-c4a1-11ec-a4da-e091533ef0ea', 
                                       'is_active': True})))
