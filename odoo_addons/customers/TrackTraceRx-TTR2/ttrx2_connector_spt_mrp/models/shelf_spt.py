from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo





class shelf_spt(models.Model):
    _name = 'shelf.spt'
    _inherit = "custom.connector.spt"
    _description = 'Shelfs'
    _inherits = {'stock.location': 'stock_location_id'}
    _OdooToTTRx = {'location_uuid': 'storage_uuid', 'parent_location_uuid': 'location_uuid', 'uuid': 'storage_shelf_uuid'}
    _TTRxToOdoo = {'uuid': 'uuid'}
    _TTRxKey = "uuid"

    stock_location_id = fields.Many2one('stock.location', 'Location', auto_join=True, index=True, ondelete="cascade", required=True)
    
    uuid = fields.Char('UUID', copy=False)
    created_on = fields.Datetime('Create On')
    last_update = fields.Datetime('Last Update')
    code = fields.Char("Code")
    parent_location_id = fields.Many2one('stock.location', 'Parent Location')
    is_default = fields.Boolean('Is Default', readonly=True)

    location_uuid = fields.Char(compute="_compute_uuid", store=False)
    parent_location_uuid = fields.Char(compute="_compute_uuid", store=False)
    
    
    def FromOdooToTTRx(self, values={}):
        location_uuid = values.get('parent_location_id') and self.env['stock.location'].\
                                browse(values['parent_location_id']).location_spt_id.uuid or \
                                self.parent_location_id.location_spt_id.uuid
        storage_area_uuid = values.get('location_id') and self.env['stock.location'].\
                                browse(values['location_id']).storage_area_spt_id.uuid or \
                                self.location_id.storage_area_spt_id.uuid
        var = {
            'uuid': location_uuid,
            'storage_area_uuid': storage_area_uuid,
            'storage_shelf_uuid': values.get('uuid', self.uuid if bool(self.uuid) else None),
            'name': values.get('name',self.name),
            'code': values.get('code',self.code or None if not bool(values) else None),
            'is_active': values.get('active',self.active),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
        parent_location_id = values.get('location_uuid') and \
            self.env['locations.management.spt'].search([('uuid','=',values['location_uuid'])],
                                                        limit=1).stock_location_id.id or None
        location_id = values.get('storage_uuid') and \
            self.env['storage.areas.spt'].search([('uuid','=',values['storage_uuid'])],
                                                 limit=1).stock_location_id.id or None
        var = {
            'uuid': values.get('storage_shelf_uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': values.get('name'),
            'code': values.get('code'),
            'active': values.get('is_active'),
            'is_default': values.get('is_default'),
            'parent_location_id': parent_location_id,
            'location_id': location_id,
            'location_type': 'storage',
        }
        CleanDataDict(var)
        return var
 
    def _compute_uuid(self):
        for reg in self:
            reg.parent_location_uuid = reg.location_id.location_spt_id.uuid
            reg.location_uuid = reg.location_id.storage_area_spt_id.uuid

    def DeleteInTTRx(self, **params):
        res = super().DeleteInTTRx(**params)
        if (not bool(res) or not bool(res.get('erro'))) and bool(self.stock_location_id):
            self.stock_location_id.unlink()
        return res

    def action_send(self):
        for reg in self:
            reg.CreateInTTRx()

    def action_refresh(self):
        for reg in self:
            reg.SyncFromTTRx(self.connector_id)

    def action_test(self):
        location_uuid = 'cb251f49-3276-41a6-9bda-eda4225b5811'
        storage_uuid = '736a901f-407c-4705-ac8a-5cc9042d6a9e'
        params = {'location_uuid': location_uuid,
                  'storage_uuid': storage_uuid}
        self.SyncFromTTRx(self.connector_id,**params)
        
