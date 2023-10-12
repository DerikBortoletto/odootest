import json
import logging

from odoo import models, fields, api
from ..tools import DateTimeToOdoo, CleanDataDict

_logger = logging.getLogger(__name__)





class manufacturers_spt(models.Model):
    _name = 'manufacturers.spt'
    _inherit = "custom.connector.spt"
    _description = 'Manufacturers'
    _TTRxKey = "tt_id"
    _OdooToTTRx = {'tt_id':'manufacturer_id'}
    _TTRxToOdoo = {'id':'tt_id'}


    res_partner_id = fields.Many2one('res.partner', 'Manufacturer Partner') # Partner Linked


    # TTRx Fields
    tt_id = fields.Char('TT ID')
    created_on = fields.Datetime('Create On')
    last_update = fields.Datetime('Create On')
    name = fields.Char("Name", required=True)
    gs1_id = fields.Char("GS1 ID")
    gs1_company_id = fields.Char("GS 1 COMPANY ID")
    gs1_sgln = fields.Char("GS 1 SGLN")
    trading_partner_uuid = fields.Char("Trading Partner UUID")
    sender_id = fields.Char("Sender ID for X12 EDI")
    receiver_id = fields.Char("Override Receiver ID for X12 EDI")
    as2_id = fields.Char("AS2ID")
    is_delegated_serial_generation = fields.Boolean("Delegated Serial Generation")
    remote_serial_source_uuid = fields.Char("Remote Serial Source UUID")
    remote_serial_source_name = fields.Char("Default Manufacturer address UUID")
    
    # Local Fields
    address_partner_id = fields.Many2one('res.partner', string='Address Partner') # Default Address
    trading_partner_address_spt_ids = fields.One2many('trading.partner.address.spt', 'res_partner_id', 'Addresses')
    
    # Post Data
    def FromOdooToTTRx(self, values={}):
        trading_partner_uuid = values.get('res_partner_id') and \
                self.env['res.partner'].search([('id','=',values['res_partner_id'])],limit=1).uuid or self.uuid
        default_address_uuid = values.get('address_partner_id') and \
                self.env['res.partner'].search([('id','=',values['address_partner_id'])],limit=1).uuid or self.uuid
        var = {
            'manufacturer_id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'name': values.get('name',self.name),
            'gs1_id': values.get('gs1_id',self.gs1_id),
            'gs1_company_id': values.get('gs1_company_id',self.gs1_company_id),
            'gs1_sgln': values.get('gs1_sgln',self.gs1_sgln),
            'trading_partner_uuid': trading_partner_uuid,
            'sender_id': values.get('sender_id',self.sender_id),
            'receiver_id': values.get('sender_id',self.sender_id),
            'as2_id': values.get('sender_id',self.sender_id),
            'is_delegated_serial_generation': values.get('sender_id',self.sender_id),
            'remote_serial_source_uuid': values.get('sender_id',self.sender_id),
            'default_address_uuid': default_address_uuid,
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
        res_partner_id = values.get('trading_partner_uuid') and \
                         self.env['res.partner'].search([('uuid','=',values['trading_partner_uuid'])],limit=1).id or None
        
        address_partner_vl = values.get('default_address_uuid')
        if bool(address_partner_vl):
            address_partner_id = address_partner_vl.get('uuid') and self.env['res.partner'].\
                                                                    search([('uuid','=',address_partner_vl['uuid'])],
                                                                           limit=1).id or None
        else:
            address_partner_id = None
        var = {
            'tt_id': values.get('id'),
            'created_on': DateTimeToOdoo(values.get('last_update')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': values.get('name'),
            'gs1_id': values.get('gs1_id'),
            'gs1_company_id': values.get('gs1_company_id'),
            'gs1_sgln': values.get('gs1_sgln'),
            'trading_partner_uuid': values.get('trading_partner_uuid'),
            'sender_id': values.get('sender_id'),
            'receiver_id': values.get('receiver_id'),
            'as2_id': values.get('as2_id'),
            'is_delegated_serial_generation': values.get('as2_id'),
            'remote_serial_source_uuid': values.get('as2_id'),
            'remote_serial_source_name': values.get('as2_id'),
            'address_partner_id': address_partner_id,
            'res_partner_id': res_partner_id,
        }
        CleanDataDict(var)
        return var

    @api.onchange('res_partner_id')
    def _onchange_res_partner_id(self):
        self.trading_partner_uuid = self.res_partner_id.ttr_uuid


    def BeforeCreateFromTTRx(self, connector, response, data):
        if not bool(data.get('res_partner_id')) and  bool(response.get('trading_partner_uuid')):
            data['res_partner_id'] = self.env['res.partner'].SyncFromTTRx(connector,uuid=response['trading_partner_uuid']).id
        return True
    
    def AfterCreateFromTTRx(self, connector, response, data):
        addresses = self.env['trading.partner.address.spt'].SyncFromTTRx(connector, primary_model='manufacturer', manufacturer_id=self.tt_id)
        
        if not self.address_partner_id and  bool(response.get('default_address_uuid')):
            context = dict(self.env.context or {})
            context['no_rewrite'] = True
            uuid = response['default_address_uuid'].get('uuid')
            if bool(uuid):
                address = self.env['trading.partner.address.spt'].SyncFromTTRx(connector,manufacturer_id=self.tt_id,
                                                                               uuid=uuid,submodal='manufacturer')
                if bool(address):
                    self.with_context(context).address_partner_id = address.res_partner_id
            if not bool(self.address_partner_id) and len(addresses) > 0:
                self.with_context(context).address_partner_id = addresses[0].res_partner_id
             
        return True

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
        self.SyncFromTTRx(self.connector_id,location_uuid='cb251f49-3276-41a6-9bda-eda4225b5811',primary_model='location')
        return True

