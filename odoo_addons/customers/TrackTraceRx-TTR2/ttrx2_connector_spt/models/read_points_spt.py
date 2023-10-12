from odoo import models, fields, api
from odoo.addons.ttrx2_connector_spt.tools import CleanDataDict, DateTimeToOdoo, DateToOdoo, StrToFloat





class read_points_spt(models.Model):
    _name = 'read.points.spt'
    _inherit = "custom.connector.spt"
    _description = 'Read Points'
    _order = 'name'
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'location_uuid': 'location_uuid', 'uuid': 'uuid'}
    _TTRxToOdoo = {'uuid': 'uuid'}
    
    uuid = fields.Char('UUID', readonly=True, copy=False, index=True)
    created_on = fields.Datetime('Create On', readonly=True, copy=False)
    last_update = fields.Datetime('Last Update', readonly=True, copy=False)
    name = fields.Char("Name", required=True)
    gs1_id = fields.Char("GS1 ID")
    active = fields.Boolean('Is Active')
    generate_api_key = fields.Boolean('Generate API Key')
    api_key_uuid = fields.Char("API Key", readonly=True)
    # line_to_an_api = fields.Char('Link to an API Key')
    locations_management_id = fields.Many2one('locations.management.spt', 'Locations', ondelete='cascade', required=True)
    connector_id = fields.Many2one('connector.spt', 'Connector')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, 
                                 default=lambda self: self.env.user.company_id)
    
    location_uuid = fields.Char(compute="_compute_uuid", store=False)

    def _compute_uuid(self):
        for reg in self:
            reg.location_uuid = reg.locations_management_id.uuid
    
    def FromOdooToTTRx(self, connector, values={}):
        if bool(values): 
            location_uuid = values.get('locations_management_id') and self.env['locations.management.spt'].\
                            brownse(values['locations_management_id']).uuid or None
        else:
            location_uuid = self.locations_management_id.uuid
            
        var = {
            'uuid': location_uuid,
            'readpoint_uuid': values.get('uuid',self.uuid),
            'name': values.get('name',str(self.name) or None if not bool(values) else None),
            'gs1_id': values.get('gs1_id',str(self.gs1_id) or None if not bool(values) else None),
            'is_active': values.get('active',self.active),
            'generate_api_key': self.generate_api_key if not bool(values) else None,
            'api_key_uuid': None,
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        locations_management_id = values.get('location_uuid') and self.env['locations.management.spt'].search(
                                                                    [('uuid','=',values['location_uuid'])],limit=1).id or None
        var = {
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': values.get('name'),
            'gs1_id': values.get('gs1_id'),
            'active': values.get('is_active'),
            'generate_api_key': values.get('generate_api_key'),
            'locations_management_id': locations_management_id,
        }
        CleanDataDict(var)
        return var
   

