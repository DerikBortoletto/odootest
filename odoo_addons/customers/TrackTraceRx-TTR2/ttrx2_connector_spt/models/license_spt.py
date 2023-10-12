import logging

from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo, StrToFloat

_logger = logging.getLogger(__name__)

PRIMARY_MODEL = [
    ('partner', 'Partner'),
    ('location', 'Location'),
    ('address', 'Adress'),
]



class license_spt(models.Model):
    _name = 'license.spt'
    _inherit = "custom.connector.spt"
    _description = 'Licenses'
    _order = 'tt_id'
    _TTRxKey = 'tt_id'
    _OdooToTTRx = {'partner': {'partner_uuid': 'partner_uuid', 'tt_id': 'id'},
                   'location': {'location_uuid': 'location_uuid', 'tt_id': 'id'},
                   'address': {'address_uuid': 'partner_uuid', 'tt_id': 'id'}}
    _TTRxToOdoo = {'id':'tt_id'}


    # TTRx Fields
    tt_id = fields.Char("TTRx2 ID", copy=False, readonly=True)
    created_on = fields.Datetime('Create On',readonly=True)
    last_update = fields.Datetime('Last Update',readonly=True)

    valid_from = fields.Date('Starting Date')
    valid_to = fields.Date('Ending Date')
    value = fields.Float("License Value", required=True)
    is_notify_client = fields.Boolean("Notify the client when this license is about to expire.", default=True, required=True)
    # is_have_attachment = fields.Boolean('Is Have Attachment')
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string='State') 
    notes = fields.Text('Note')
    
    # odoo2ttrx & ttrx2ttrx Fields
    license_type = fields.Many2one('license.types.management.spt', string="License Type", copy=False)
    locations_management_id = fields.Many2one('locations.management.spt', string='Locations')
    address_id = fields.Many2one('trading.partner.address.spt', string='Address')
    res_partner_id = fields.Many2one('res.partner', 'Partner')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one('res.country.state', 'state')

    # Odoo Fields
    active = fields.Boolean("Active", default=True)
    
    # Attachments #
    license_attachments_spt_ids = fields.One2many('license.attachments.spt', 'license_spt_id', 'License Attachments')
    
    partner_uuid = fields.Char(compute="_compute_uuid", store=False)
    location_uuid = fields.Char(compute="_compute_uuid", store=False)
    address_uuid = fields.Char(compute="_compute_uuid", store=False)
    
    primary_model = fields.Selection(PRIMARY_MODEL, string='Primary model')
    
    def _compute_uuid(self):
        for reg in self:
            reg.location_uuid = reg.locations_management_id.uuid
            reg.partner_uuid = reg.res_partner_id.uuid
            reg.address_uuid = reg.address_id.uuid

    # Funções De/Para    

    def FromOdooToTTRx(self, connector, values={}):
        primary_model = values.get('primary_model',self.primary_model)
        license_type_id = values.get('license_type') and \
                          self.env['license.types.management.spt'].search([('id','=',values['license_type'])],limit=1).lic_id or \
                          self.license_type.lic_id
        if bool(values):
            res_country = values.get('country_id') and \
                        self.env['res.country'].search([('id','=',values['country_id'])],limit=1) or None
            res_state = values.get('res_country_state_id') and \
                        self.env['res.country.state'].search([('id','=',values['res_country_state_id'])],limit=1) or None
        else:
            res_country = self.country_id
            res_state = self.state_id

        if bool(res_country) and res_country.code in ['CA','US']:
            res_state_cd = res_state.code if bool(res_state) else None
        else:
            res_state_cd = res_state.name if bool(res_state) else None
            
        res_country_cd = res_country.code if bool(res_country) else None

        uuid = False
        if primary_model == 'partner':
            uuid = values.get('res_partner_id') and self.env['res_partner'].\
                                                    browse(values['res_partner_id']).uuid or self.res_partner_id.uuid
        elif primary_model == 'location':
            uuid = values.get('locations_management_id') and self.env['res_partner'].\
                                                             browse(values['locations_management_id']).uuid or \
                                                             self.locations_management_id.uuid
        elif primary_model == 'address':
            uuid = values.get('address_id') and self.env['trading.partner.address.spt'].\
                                                browse(values['address_id']).uuid or self.address_id.uuid

            
        var = {
            'uuid': uuid,
            'id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'valid_from': values.get('valid_from',self.valid_from),
            'valid_to': values.get('valid_to',self.valid_to),
            'value': values.get('value',self.value),
            'is_notify_client': values.get('is_notify_client',self.is_notify_client),
            'is_archived': values.get('active',self.active),
            'notes': values.get('notes',self.notes),
            'licence_type_id': license_type_id,
            'country_code': res_country_cd,
            'state': res_state_cd,
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        license_type_id = None
        if bool(values.get('licence_type')) and bool(values['licence_type'].get('id')):
                license_type_id = self.env['license.types.management.spt'].\
                                  search([('lic_id','=',values['licence_type']['id'])],limit=1).id or None
        res_country = values.get('country_code') and self.env['res.country'].search([('code','=',values['country_code'])],limit=1)
        if bool(res_country) and res_country.code in ['CA','US']:
            res_country_state = values.get('state_code') and \
                                self.env['res.country.state'].search([('country_id','=',res_country.id),
                                                                      ('code','=',values['state_code'])],limit=1) or None
        elif bool(res_country):
            res_country_state = values.get('state_name') and \
                                self.env['res.country.state'].search([('country_id','=',res_country.id),
                                                                      ('name','ilike',values['state_name'])],limit=1) or None
        else:
            res_country_state = None

        locations_management_id = values.get('location_uuid') and \
            self.env['locations.management.spt'].search([('uuid','=',values['location_uuid'])],limit=1).id or None

        primary_model = values.get('primary_model')
        if bool(locations_management_id):
            if not bool(primary_model): primary_model = 'location'
            res_partner_id = self.env.company.partner_id.id
        else:
            res_partner_id = values.get('partner_uuid') and \
                self.env['res.partner'].search([('uuid','=',values['partner_uuid'])],limit=1).id or None
            if bool(res_partner_id):
                if not bool(primary_model): primary_model = 'partner'
            
        address_id = values.get('address_uuid') and \
            self.env['trading.partner.address.spt'].search([('uuid','=',values['address_uuid'])],limit=1).id or None
        if bool(res_partner_id):
            if not bool(primary_model): primary_model = 'address'
        
        var = {
            'tt_id': values.get('id'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'valid_from': DateToOdoo(values.get('valid_from')),
            'valid_to': DateToOdoo(values.get('valid_to')),
            'value': StrToFloat(values.get('value')) if bool(values.get('value')) else None,
            'is_notify_client': values.get('is_notify_client'),
            'active': values['is_archived'] if bool(values.get('is_archived',False)) else None,
            'notes': values.get('notes'),
            'license_type': license_type_id,
            'country_id': res_country.id if bool(res_country) else None,
            'state_id': res_country_state.id if bool(res_country_state) else None,
            'license_ttrx_type': values.get('license_ttrx_type'), # Just in Odoo
            'res_partner_id': res_partner_id,# Just in Odoo
            'locations_management_id': locations_management_id, # Just in Odoo
            'address_id': address_id,
            'primary_model': primary_model, # Just in Odoo
        }
        CleanDataDict(var)
        return var

        
    def AfterCreateFromTTRx(self, connector, response, data):
        if bool(self.res_partner_id.uuid):
            self.env['license.attachments.spt'].SyncFromTTRx(connector,partner_uuid=self.res_partner_id.uuid, licence_id=self.tt_id)
        return True

    def AfterWriteFromTTRx(self, connector, response, data):
        self.env['license.attachments.spt'].SyncFromTTRx(connector,partner_uuid=self.res_partner_id.uuid, licence_id=self.tt_id)
        return True
    
    def action_send(self):
        for reg in self:
            reg.CreateInTTRx()
        return True

    def action_test(self):
        # 'location': {'location_uuid': 'location_uuid', 'tt_id': 'id'}
        self.SyncFromTTRx(self.connector_id,location_uuid='cb251f49-3276-41a6-9bda-eda4225b5811',primary_model='location')
        return True
