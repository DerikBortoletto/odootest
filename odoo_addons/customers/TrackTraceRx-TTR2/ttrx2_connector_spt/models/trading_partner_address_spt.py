import logging

from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo


_logger = logging.getLogger(__name__)


PRIMARY_MODEL = [
    ('partner', 'Partner'),
    ('location', 'Location'),
    ('manufacturer', 'Manufacturer'),
]



class trading_partner_address_spt(models.Model):
    _name = 'trading.partner.address.spt'
    _inherit = "custom.connector.spt"
    _description = 'Addresses of partners'
    _rec_name = 'address_nickname'
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'partner': {'partner_uuid': 'partner_uuid', 'uuid': 'uuid'},
                   'location': {'location_uuid': 'location_uuid', 'uuid': 'uuid'},
                   'manufacturer': {'manufacture_sp_id': 'manufacturer_id', 'uuid': 'uuid'}}
    _TTRxToOdoo = {'uuid': 'uuid'}


    res_partner_id = fields.Many2one('res.partner', 'Trading Partner') # Partner Linked

    # TTRx2 Fields    
    uuid = fields.Char("UUID", readonly=True, copy=False, index=True)
    created_on = fields.Datetime('Create On', readonly=True)
    last_update = fields.Datetime('Last Update', readonly=True)
    gs1_id = fields.Char("Address GSL")
    address_nickname = fields.Char("Nickname")
    recipient_name = fields.Char("Recipient Name")
    line1 = fields.Char("Line 1")
    line2 = fields.Char("Line 2")
    line3 = fields.Char("Line 3")
    line4 = fields.Char("Line 4")
    res_country_id = fields.Many2one('res.country', 'Country')
    res_country_state_id = fields.Many2one('res.country.state', 'State')
    city = fields.Char('City')
    zip = fields.Char('ZIP/Postal Code')
    phone = fields.Char('Phone')
    phone_ext = fields.Char('Ext Phone')
    email = fields.Char("Email")
    address_ref = fields.Char("Address Ref")
    is_default_address = fields.Boolean("Default Address")
    is_licence_required = fields.Boolean("Licence Required")

    # Foreign key
    address_partner_id = fields.Many2one('res.partner', 'Address Partner') # Deafult Address
    locations_management_id = fields.Many2one('locations.management.spt', 'Location', ondelete='cascade')
    manufacturer_id = fields.Many2one('manufacturers.spt', 'Manufacturer', ondelete='cascade')
    # # address_owner = fields.Selection([('1','Trading Partner'),('2','Location'),('3','Manufacturer')])
    # connector_id = fields.Many2one('connector.spt', 'Connector')
    # company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, 
    #                              default=lambda self: self.env.user.company_id)
    
    partner_uuid = fields.Char(compute="_compute_uuid", store=False)
    location_uuid = fields.Char(compute="_compute_uuid", store=False)
    manufacturer_sp_id = fields.Char(compute="_compute_uuid", store=False)
    primary_model = fields.Selection(PRIMARY_MODEL, string='Primary model')

    def _compute_uuid(self):
        for reg in self:
            reg.location_uuid = reg.locations_management_id.uuid
            reg.partner_uuid = reg.address_partner_id.uuid
            reg.manufacturer_sp_id = reg.manufacturer_id.tt_id
    
    
    def FromOdooToTTRx(self, connector, values={}):
        primary_model = values.get('primary_model',self.primary_model)
        if bool(values):
            res_country = values.get('res_country_id') and self.env['res.country'].\
                          search([('id','=',values['res_country_id'])], limit=1) or None
            res_state = values.get('res_country_state_id') and self.env['res.country.state'].\
                          search([('id','=',values['res_country_state_id'])], limit=1) or None
        else:
            res_country = self.res_country_id
            res_state = self.res_country_state_id
        if bool(res_state):
            if bool(res_country) and res_country.code in ['CA','US']:
                res_state_cd = res_state.code or None
            else:
                res_state_cd = res_state.name or None
        else:
            res_state_cd = None
        res_country_cd = res_country.code if bool(res_country) else None

        manufacturer_id = None
        address_uuid = None
        location_uuid = None
        
        if primary_model == 'partner':
            address_uuid = values.get('address_partner_id') and \
                   self.env['res_partner'].browse(values['address_partner_id']).uuid or self.address_partner_id.uuid
        elif primary_model == 'location':
            location_uuid = values.get('locations_management_id') and \
                   self.env['res_partner'].browse(values['locations_management_id']).uuid or self.locations_management_id.uuid
        elif primary_model == 'manufacturer':
            manufacturer_id = values.get('manufacturer_id') and \
                   self.env['manufacturers.spt'].browse(values['manufacturer_id']).uuid or self.manufacturer_id.id

        var = {
            'uuid': values.get('uuid',self.uuid if bool(self.uuid) else None),
            'address_uuid': address_uuid,
            'location_uuid': location_uuid,
            'manufacturer_id': manufacturer_id,
            'address_gs1_id': values.get('gs1_id',self.gs1_id) or None,
            'address_nickname': values.get('address_nickname',self.address_nickname) or None,
            'recipient_name': values.get('recipient_name',self.recipient_name) or None,
            'line1': values.get('line1',self.line1) or None,
            'line2': values.get('line2',self.line2) or None,
            'line3': values.get('line3',self.line3) or None,
            'line4': values.get('line4',self.line4) or None,
            'country_code': res_country_cd,
            'state': res_state_cd,
            'city': values.get('city',self.city) or None,
            'zip': values.get('zip',self.zip) or None,
            'phone': values.get('phone',self.phone) or None,
            'phone_ext': values.get('phone_ext',self.phone_ext) or None,
            'email': values.get('email',self.email) or None,
            'address_ref': values.get('address_ref',self.address_ref) or None,
            'is_licence_required': values.get('is_licence_required',self.is_licence_required),
            'is_default_address': values.get('is_default_address', self.is_default_address),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        primary_model = values.get('primary_model')
        if not bool(primary_model):
            if values.get('partner_uuid'):
                primary_model = PRIMARY_MODEL[0]
            elif values.get('location_uuid'):
                primary_model = PRIMARY_MODEL[1]
            elif values.get('manufacturer_id'):
                primary_model = PRIMARY_MODEL[2]
        res_country = values.get('country_code') and \
                      self.env['res.country'].search([('code','=',values['country_code'])],limit=1) or None
        if bool(res_country) and res_country.code in ['CA','US']:
            res_country_state = values.get('state_code') and \
                      self.env['res.country.state'].search([('country_id','=',res_country.id),
                                                            ('code','=',values['state_code'])],limit=1) or None
        elif bool(res_country):
            res_country_state = values.get('state') and self.env['res.country.state'].search([('country_id','=',res_country.id),
                                                                      ('code','ilike',values['state'])],limit=1) or None
        else:
            res_country_state = None

        locations_management_id = None
        if values.get('location_uuid') != None:
            locations_management_id = values.get('location_uuid') and \
                self.env['locations.management.spt'].search([('uuid','=',values['location_uuid'])],limit=1).id or None

        address_partner_id = None
        if bool(locations_management_id):
            address_partner_id = self.env.company.partner_id.id
        elif values.get('partner_uuid') != None:
            address_partner_id = values.get('partner_uuid') and \
                self.env['res.partner'].search([('uuid','=',values['partner_uuid'])],limit=1).id or None

        manufacturer_id = values.get('manufacturer_id') and \
                self.env['manufacturers.spt'].search([('tt_id','=',values['manufacturer_id'])],limit=1).id or None
        if bool(manufacturer_id) and not bool(address_partner_id):
            address_partner_id = self.env['manufacturers.spt'].browse(manufacturer_id).res_partner_id.id

        var = {
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'gs1_id': values.get('gs1_id'),
            'address_nickname': values.get('address_nickname'),
            'recipient_name': values.get('recipient_name'),
            'line1': values.get('line1'),
            'line2': values.get('line2'),
            'line3': values.get('line3'),
            'line4': values.get('line4'),
            'res_country_id': res_country.id if bool(res_country) else None,
            'res_country_state_id': res_country_state.id if bool(res_country_state) else None,
            'city': values.get('city'),
            'zip': values.get('zip'),
            'phone': values.get('phone'),
            'phone_ext': values.get('phone_ext'),
            'email': values.get('email'),
            'address_ref': values.get('address_ref'),
            'is_default_address': values.get('is_default_address'),
            'is_licence_required': values.get('is_licence_required'),
            'address_owner': values.get('address_owner'),
            'locations_management_id': locations_management_id,
            'address_partner_id': address_partner_id,
            'manufacturer_id': manufacturer_id,
            'primary_model': primary_model,
            
        }
        CleanDataDict(var)
        return var

    def AfterCreateFromTTRx(self, connector, response, data):
        if bool(self):
            self.UpdateCreateResPartner(connector=connector, response=response, data=data)
            self.env['license.spt'].SyncFromTTRx(connector,primary_model='address',address_uuid=self.uuid)
        return True

    def AfterWriteFromTTRx(self, connector, response, data):
        if bool(self):
            self.UpdateCreateResPartner(connector=connector, response=response, data=data)
        return True
        

    def UpdateCreateResPartner(self, connector, response, data):
        partner_id = None
        if self.primary_model == 'partner':
            partner_id = self.address_partner_id.id
            type = 'other'
        elif self.primary_model == 'location':
            partner_id = self.env.company.partner_id.id
            type = 'delivery'
        elif self.primary_model == 'manufacturer': 
            partner_id = self.manufacturer_id.res_partner_id.id
            type = 'other'
        var = {
            'type': type,
            'type_ttr': 'TRADING_PARTNER_CONTACT_ADDRESS',
            'company_type': 'person',
            'uuid': self.uuid,
            'name': self.recipient_name,
            'parent_id': partner_id,
            'friendly_name': self.address_nickname,
            'street': self.line1,
            'street2': self.line2,
            'city': self.city,
            'zip': self.zip,
            'state_id': self.res_country_state_id.id,
            'country_id': self.res_country_id.id,
            'phone': self.phone + ' ext ' + self.phone_ext if bool(self.phone_ext) else self.phone,
            'email': self.email,
        }
        exists = self.res_partner_id or self.env['res.partner'].search([('uuid','=',self.uuid)],limit=1)
        context = dict(self.env.context or {})
        context['no_rewrite'] = True
        if exists: 
            exists.with_context(context).write(var)
            self.with_context(context).res_partner_id = exists
        else:
            exists = self.env['res.partner'].create(var)
            self.with_context(context).res_partner_id = exists

    def action_send(self):
        for reg in self:
            reg.CreateInTTRx(connector=reg.connector_id)
        return True

    def action_refresh(self):
        for reg in self:
            reg.SyncFromTTRx(self.connector_id,type='delivery',ForceUpdate=True,primary_model='location')
        return True

    def action_test(self):
        # 'location': {'location_uuid': 'location_uuid', 'tt_id': 'id'}
        self.env['trading.partner.users.spt'].SyncFromTTRx(self.connector_id,partner_uuid='47e2a1c5-3eee-484b-93ef-1632f12f5388')
        return True


