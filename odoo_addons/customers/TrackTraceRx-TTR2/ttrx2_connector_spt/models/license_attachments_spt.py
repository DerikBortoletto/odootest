import base64
import json
import urllib
import urllib.request as urllib2
from datetime import datetime

from odoo import models, fields, api
from ..tools import DateTimeToOdoo, CleanDataDict

PRIMARY_MODEL = [
    ('partner', 'Partner'),
    ('location', 'Location'),
    ('address', 'Adress'),
]


class license_attachments_spt(models.Model):
    _name = "license.attachments.spt"
    _inherit = "custom.connector.spt"
    _inherits = {'ir.attachment': 'attachment_id'}
    _order = 'license_spt_id,tt_id'
    _description = 'Model for TTR'
    _TTRxKey = 'tt_id'
    _OdooToTTRx = {'partner': {'partner_uuid': 'partner_uuid', 'licence_id': 'licence_id', 'tt_id': 'attachment_id'},
                   'location': {'location_uuid': 'location_uuid', 'licence_id': 'licence_id', 'tt_id': 'attachment_id'},
                   'address': {'address_uuid': 'address_uuid', 'licence_id': 'licence_id', 'attachment_id': 'attachment_id'}}
    _TTRxToOdoo = {'id':'tt_id'}

    attachment_id = fields.Many2one('ir.attachment', 'Attachment', auto_join=True, index=True, ondelete="cascade", required=True)

    tt_id = fields.Char("TTRx2 ID", copy=False)
    created_on = fields.Datetime('Create On')
    last_update = fields.Datetime('Last Update')
    
    license_spt_id = fields.Many2one('license.spt', 'License', ondelete='cascade')
    connector_id = fields.Many2one('connector.spt', 'Connector')

    partner_uuid = fields.Char(compute="_compute_uuid", store=False)
    location_uuid = fields.Char(compute="_compute_uuid", store=False)
    address_uuid = fields.Char(compute="_compute_uuid", store=False)
    licence_id = fields.Char(compute="_compute_uuid", store=False) 

    primary_model = fields.Selection(PRIMARY_MODEL, string='Primary model')

    def _compute_uuid(self):
        for reg in self:
            reg.partner_uuid = reg.license_spt_id.res_partner_id.uuid
            reg.location_uuid = reg.license_spt_id.locations_management_id.uuid
            reg.address_uuid = reg.license_spt_id.address_id.uuid
            reg.licence_id = reg.license_spt_id.tt_id

    #TODO: Fazer o inherits com  com o Odoo
    
    def FromOdooToTTRx(self, connector, values={}):
        if bool(values):
            license_spt = values.get('license_spt_id') and self.env['license.spt'].browse(values['license_spt_id']) or None
        else:
            license_spt = self.license_spt_id
        license_id = None
        partner_uuid = None
        location_uuid = None
        address_uuid = None
        if bool(license_spt):
            partner_uuid = license_spt.res_partner_id.uuid
            license_id = license_spt.tt_id
        var = {
            'uuid': partner_uuid or location_uuid or address_uuid,
            'id': license_id,
            'attachment_id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'name': values.get('name',self.name or None if not bool(values) else None),
            'file': values.get('datas',self.datas or None if not bool(values) else None),
            'notes': values.get('description'),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        primary_model = values.get('primary_model')
        partner = values.get('partner_uuid') and self.env['res.partner'].search([('uuid','=',values['partner_uuid'])],limit=1) or None
        location = values.get('location_uuid') and self.env['locations.management.spt'].search([('uuid','=',values['location_uuid'])],limit=1) or None
        address = values.get('address_uuid') and self.env['trading.partner.address.spt'].search([('uuid','=',values['address_uuid'])],limit=1).id or None
        license_spt_id = None
        if bool(partner) and values.get('licence_id'):
            license_spt_id = self.env['license.spt'].search([('res_partner_id','=',partner.id),('tt_id','=',values.get('licence_id'))]) or None
        elif bool(location) and values.get('licence_id'):
            license_spt_id = self.env['license.spt'].search([('locations_management_id','=',location.id),('tt_id','=',values.get('licence_id'))]) or None
        elif bool(address) and values.get('licence_id'):
            license_spt_id = self.env['license.spt'].search([('address_id','=',address.id),('tt_id','=',values.get('licence_id'))]) or None
        
        var = {
            'tt_id': values.get('id'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'primary_model': primary_model,
            'name': values.get('name'),
            'description': values.get('notes'),
            'type': 'binary' if bool(values.get('fileext')) else None,
            'datas': base64.encodebytes(values['fileext']) if bool(values.get('fileext')) else None,
            'res_model': 'license.spt' if bool(values.get('fileext')) else None,
            'res_id': license_spt_id,
            'license_spt_id': license_spt_id,
        }
        CleanDataDict(var)
        return var
    
