from odoo import models, fields, api
from odoo.exceptions import UserError
from ..tools import DateTimeToOdoo, CleanDataDict
from ..connector.service import get_uri

CONTAINER_TYPE = [
    ('UUID','UUID'),
    ('SERIAL','Serial'),
    ('GS1_ID_SERIAL','GS1_ID Serial'),
]


class dispositions_spt(models.Model):
    _name = 'disposition.spt'
    _inherit = "custom.connector.spt"
    _description = "List of Dispositions for EPCIS"
    _order = 'name'
    _TTRxKey = 'tt_id'
    _OdooToTTRx = {'tt_id':'id'}
    _TTRxToOdoo = {'id': 'tt_id'}

    
    tt_id = fields.Char('TT ID')
    name = fields.Char('Name')
    uri = fields.Char("URI")
    is_internal = fields.Boolean('Is internal')
    connector_id = fields.Many2one('connector.spt', 'Connector')

    def FromTTRxToOdoo(self, connector, values):
        var = {
            'tt_id': values.get('id'),
            'name': values.get('name'),
            'uri': values.get('uri'),
            'is_internal': values.get('is_internal'),
        }
        CleanDataDict(var)
        return var
    

class business_step_spt(models.Model):
    _name = 'business.step.spt'
    _inherit = "custom.connector.spt"
    _description = "List of Business Steps for EPCIS"
    _order = 'name'
    _TTRxKey = 'tt_id'
    _OdooToTTRx = {'tt_id':'id'}
    
    tt_id = fields.Char('TT ID')
    name = fields.Char('Name')
    uri = fields.Char("URI")
    is_internal = fields.Boolean('Is internal')
    connector_id = fields.Many2one('connector.spt', 'Connector')

    def FromTTRxToOdoo(self, connector, values):
        var = {
            'tt_id': values.get('id'),
            'name': values.get('name'),
            'uri': values.get('uri'),
            'is_internal': values.get('is_internal'),
        }
        CleanDataDict(var)
        return var
    

class container_spt(models.Model):
    _name = 'container.spt'
    _inherit = "custom.connector.spt"
    _description = "TTRx2 Container"
    _inherits = {'stock.quant.package': 'package_id'}
    _order = 'location_area_id,storage_area_id,uuid'
    _TTRxKey = "uuid"
    _OdooToTTRx = {'container_id_type':'container_id_type', 'container_identifier': 'container_identifier'}
    _TTRxToOdoo = {'uuid':'uuid'}


    package_id = fields.Many2one('stock.quant.package', string='Package', auto_join=True, index=True, ondelete="cascade", required=True)

    # TTR2 Fields
    
    # container_identifier => name
    container_id_type = fields.Selection(CONTAINER_TYPE, 'Container ID', default='UUID')
    container_identifier = fields.Char('Container Id', compute="_compute_identifier", store=True, index=True, readonly=True)

    uuid = fields.Char('UUID', copy=False, readonly=True)
    gs1_unique_id = fields.Char('GS1 Unique Serial ID')

    container_type_id = fields.Many2one('pack.size.type.spt', string='Type of Container')
    parent_id = fields.Many2one('container.spt', string='Parent Container')
    location_area_id = fields.Many2one('locations.management.spt', string='Location', required=True)
    storage_area_id = fields.Many2one('storage.areas.spt', string='Storage Area', required=True)
    storage_shelf_id = fields.Many2one('shelf.spt', string='Storage Shelf')
    disposition_id = fields.Many2one('disposition.spt', string='Disposition')
    business_step_id = fields.Many2one('business.step.spt', string='Business step')

    @api.depends('container_id_type')
    def _compute_identifier(self):
        for reg in self:
            if reg.container_id_type == 'UUID':
                reg.container_identifier = reg.uuid
            elif reg.container_id_type == 'SERIAL':
                reg.container_identifier = reg.name
            elif reg.container_id_type == 'GS1_ID_SERIAL':
                reg.container_identifier = reg.serial
            else:
                reg.container_identifier = False

    @api.onchange('storage_area_id')
    def on_change_storage_area_id(self):
        self.location_area_id = self.storage_area_id.location_id.location_spt_id
        self.location_id = self.storage_area_id.location_id

    def FromOdooToTTRx(self, connector, values={}):
        parent_container_gs1_id_unique_serial = values.get('parent_id') and \
                                                self.browse(values['parent_id']).name or self.parent_id.name
        container_type_id = values.get('container_type_id') and \
                            self.env['pack.size.type.spt'].browse(values['container_type_id']).tt_id or self.container_type_id.tt_id
        location_uuid = values.get('location_area_id') and \
                        self.env['locations.management.spt'].browse(values['location_area_id']).uuid or self.location_area_id.uuid
        storage_area_uuid = values.get('storage_area_id') and \
                            self.env['storage.areas.spt'].browse(values['storage_area_id']).uuid or self.storage_area_id.uuid
        storage_shelf_uuid = values.get('storage_shelf_id') and \
                             self.env['shelf.spt'].browse(values['storage_shelf_id']).uuid or self.storage_shelf_id.uuid
        disposition_id = values.get('disposition_id') and \
                         self.env['disposition.spt'].browse(values['disposition_id']).tt_id or self.disposition_id.tt_id
        business_step_id = values.get('business_step_id') and \
                           self.env['business.step.spt'].browse(values['business_step_id']).tt_id or self.business_step_id.tt_id
            
        var = {
            'container_type_id': container_type_id or '',
            'gs1_id_unique_serial': values.get('gs1_unique_id',self.gs1_unique_id) or '',
            'unique_serial': values.get('name',self.name) or '',
            'parent_container_gs1_id_unique_serial': parent_container_gs1_id_unique_serial or '',
            'location_uuid': location_uuid,
            'storage_area_uuid': storage_area_uuid,
            'storage_shelf_uuid': storage_shelf_uuid or '',
            'disposition_id': disposition_id or '',
            'business_step_id': business_step_id or '',
            'container_id_type': self.container_id_type or '',
            'container_identifier': self.container_identifier or '',
        }
        CleanDataDict(var)
        return var
    
    def FromTTRxToOdoo(self, connector, values):
        
        storage_area_id = values.get('storage_area_uuid') and \
                          self.env['storage.areas.spt'].search([('uuid','=',values['storage_area_uuid'])],limit=1).id or None
        storage_shelf_id = values.get('storage_shelf_uuid') and \
                           self.env['shelf.spt'].search([('uuid','=',values['storage_shelf_uuid'])],limit=1).id or None
        container_type_id = values.get('packaging_type_id') and \
                            self.env['pack.size.type.spt'].search([('tt_id','=',values['packaging_type_id'])],limit=1).id or None
        location_area_id = values.get('location_uuid') and \
                           self.env['locations.management.spt'].search([('uuid','=',values['location_uuid'])],limit=1).id or None
        parent_id = values.get('parent_uuid') and \
                    self.env['container.spt'].search([('uuid','=',values['parent_uuid'])],limit=1).id or None
                    
        if parent_id == None:
            parent_id = values.get('parent_serial') and self.env['container.spt'].\
                                                    search([('serial','=',values['parent_serial'])],limit=1) or None
        if parent_id == None:
            parent_id = values.get('parent_gs1_unique_id') and self.env['container.spt'].\
                                                    search([('gs1_unique_id','=',values['parent_gs1_unique_id'])],limit=1) or None

        disposition_id = values.get('disposition_id') and self.env['disposition.spt'].\
                                                    search([('tt_id','=',values['disposition_id'])],limit=1).id or None
        business_step_id = values.get('business_step_id') and self.env['business.step.spt'].\
                                                    search([('tt_id','=',values['business_step_id'])],limit=1).id or None
        var = {
            'uuid': values.get('uuid'),
            'name': values.get('serial'),
            'gs1_unique_id': values.get('gs1_unique_id'),
            'container_type_id': container_type_id,
            'parent_id': parent_id,
            'location_area_id': location_area_id,
            'storage_area_id': storage_area_id,
            'storage_shelf_id':storage_shelf_id,
            'disposition_id': disposition_id,
            'business_step_id': business_step_id,
        }
        CleanDataDict(var)
        return var

    def SyncFromTTRx(self, connector, **params):
        self.ensure_one
        res = self.env[self._name]
        MySelf = bool(params.get('MySelf',False))
        if MySelf:
            res += self._CreateUpdateFromTTRx(connector, \
                                             container_id_type=self.container_id_type, \
                                             container_identifier=self.container_identifier)
        else:
            resource = self._name
            data_list = self._GetList(connector, resource+'.list', **params) or []
            for data in data_list:
                for key in params.keys():
                    if not bool(params.get(key,False)):
                        params[key] = data.get(key,params[key])
                params.update(data)
                params.update({'container_id_type': 'UUID', 'container_identifier': data['container_uuid']})
                res += self._CreateUpdateFromTTRx(connector, **params)
        return res

    def CreateInTTRx(self, **params):
        self.ensure_one
        params = {}

        if not bool(self.uuid):
            params['data'] = self.FromOdooToTTRx(connector=self.connector_id)
            params.update(self._GetUriParams(self._name))
            self.BeforeCreateInTTRx(**params)
            create_response = self._PostRecord(self.connector_id, self._name+'.post', **params) 
            if bool(create_response) and not bool(create_response.get('erro')):
                context = dict(self.env.context or {})
                context['no_rewrite'] = True
                self.with_context(context).write(create_response)
            self.AfterCreateInTTRx(**params)
        return True

    def BeforeCreateFromTTRx(self, connector, response, data):
        self.env['disposition.spt'].SyncFromTTRx(connector)
        self.env['business.step.spt'].SyncFromTTRx(connector)
        if not bool(data.get('location_area_id')) and bool(response.get('location_uuid')):
            data['location_area_id'] = self.env['locations.management.spt'].SyncFromTTRx(connector,uuid=response['location_uuid']).id
        if not bool(data.get('storage_area_id')) and bool(response.get('storage_area_uuid')):
            data['storage_area_id'] = self.env['storage.areas.spt'].SyncFromTTRx(connector,uuid=response['storage_area_uuid']).id
        if not bool(data.get('storage_shelf_id')) and bool(response.get('storage_shelf_uuid')):
            data['storage_shelf_id'] = self.env['shelf.spt'].SyncFromTTRx(connector,uuid=response['storage_shelf_uuid'])
        return True
    
    def action_send(self):
        for reg in self:
            reg.CreateInTTRx()
        return True

    def action_refresh(self):
        for reg in self:
            reg.SyncFromTTRx(self.connector_id,MySelf=True)
        return True

    def action_test(self):
        # 'location': {'location_uuid': 'location_uuid', 'tt_id': 'id'}
        self.SyncFromTTRx(self.connector_id)
        return True
