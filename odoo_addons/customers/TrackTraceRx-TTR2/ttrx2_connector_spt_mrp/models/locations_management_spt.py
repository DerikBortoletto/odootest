import logging

from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo

_logger = logging.getLogger(__name__)





class locations_management_spt(models.Model):
    _name = 'locations.management.spt'
    _inherit = "custom.connector.spt"
    _description = 'Locations Management'
    _inherits = {'stock.location': 'stock_location_id'}
    _TTRxKey = "uuid"
    _OdooToTTRx = {'uuid':'uuid'}
    _TTRxToOdoo = {'uuid':'uuid'}

    stock_location_id = fields.Many2one('stock.location', 'Location', auto_join=True, index=True, ondelete="cascade", required=True)

      
    # Fields in TTRx
    uuid = fields.Char('UUID', copy=False)
    created_on = fields.Datetime('Create On', readonly=True, copy=False)
    last_update = fields.Datetime('Last Update', readonly=True, copy=False)
    gs1_id = fields.Char("GLN")
    gs1_sgln = fields.Char("GSI SGLN")
    location_detail = fields.Char("Location Detail")
    is_unselectable_location = fields.Boolean("Is Unselectable Location", default=False, required=True)
    is_virtual = fields.Boolean("Is Virtual Location", default=False)
    manufacturing_location_id = fields.Char("Manufacturing Location ID") 

    # Parent id
    default_address_id = fields.Many2one('trading.partner.address.spt', 'Default Address') 
    
    # Join
    license_ids = fields.One2many('license.spt', 'locations_management_id', 'Licenses')
    address_ids = fields.One2many('trading.partner.address.spt', 'locations_management_id', 'Addresses')
    read_points_ids = fields.One2many('read.points.spt', 'locations_management_id', 'Read Points')

    def FromOdooToTTRx(self, values={}):
        var = super(locations_management_spt,self).FromOdooToTTRx(values=values)
        if bool(values):
            parent_location_uuid = values.get('location_id') and \
                                   self.env['stock.location'].browse(values['location_id']).location_spt_id.uuid or None
        else:
            parent_location_uuid = self.location_id.location_spt_id.uuid
        var.update({
            'uuid': values.get('uuid',self.uuid if bool(self.uuid) else None),
            'gs1_id': values.get('gs1_id',self.gs1_id or None if not bool(values) else None),
            'gs1_sgln': values.get('gs1_sgln',self.gs1_sgln or None if not bool(values) else None),
            'name': values.get('name',self.name),
            'location_detail': values.get('location_detail',self.location_detail or None if not bool(values) else None),
            'is_unselectable_location': values.get('is_unselectable_location',self.is_unselectable_location),
            'is_active': values.get('active',self.active),
            'parent_location_uuid': parent_location_uuid,
            'notes': values.get('notes',self.notes or None if not bool(values) else None),
            'create_default_storage_area': None,
        })
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
        var = super(locations_management_spt,self).FromOdooToTTRx(values=values)
        location_id = bool(values.get('parent_location_uuid')) and self.env['locations.management.spt'].\
                             search([('uuid','=',values['parent_location_uuid'])],limit=1).stock_location_id.id or None
        default_address_id = bool(values.get('default_address_uuid')) and self.env['trading.partner.address.spt'].\
                            search([('uuid','=',values['default_address_uuid'])],limit=1).id or None 
        var.update({
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'gs1_id': values.get('gs1_id'),
            'gs1_sgln': values.get('gs1_sgln'),
            'name': values.get('name'),
            'location_detail': values.get('location_detail'),
            'is_unselectable_location': values.get('is_unselectable_location'),
            'notes': values.get('notes'),
            'active': values.get('is_active'),
            'location_id': location_id,
            'default_address_id': default_address_id,
            'location_type': 'sub' if bool(location_id) else 'main',
        })
        CleanDataDict(var)
        return var

    def BeforeCreateFromTTRx(self, connector, response, data):
        if not bool(data.get('location_id')) and  bool(response.get('parent_location_uuid')):
            data['location_id'] = self.env['locations.management.spt'].\
                                  SyncFromTTRx(connector,uuid=response['parent_location_uuid']).id

    def AfterCreateFromTTRx(self, connector, response, data):
        # self.env['trading.partner.address.spt'].SyncFromTTRx(connector, primary_model='location', location_uuid=self.uuid)
        self.env['storage.areas.spt'].SyncFromTTRx(connector, location_uuid=self.uuid)
        self.env['license.spt'].SyncFromTTRx(connector, primary_model='location', location_uuid=self.uuid)
        self.env['read.points.spt'].SyncFromTTRx(connector, location_uuid=self.uuid)
        
        context = dict(self.env.context or {})
        context['no_rewrite'] = True
        if not self.default_address_id and not bool(data.get('default_address_id')) and  bool(response.get('default_address_uuid')):
            adress_id = self.env['trading.partner.address.spt'].SyncFromTTRx(connector,location_uuid=self.uuid,
                                                                             uuid=response['default_address_uuid'],
                                                                             submodal='location')
            self.with_context(context).default_address_id = adress_id
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

    def action_refresh(self):
        for reg in self:
            reg.SyncFromTTRx(self.connector_id,myown=True)
        return True

    def action_test(self):
        return True

    