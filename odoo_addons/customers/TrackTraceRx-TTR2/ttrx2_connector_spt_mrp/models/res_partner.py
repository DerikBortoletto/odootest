import logging

from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo


_logger = logging.getLogger(__name__)



TTRX_TYPE = [
    ('VENDOR', 'Vendor'),
    ('CUSTOMER', 'Customer'), 
    ('MANUFACTURER', 'Manufacturer'),
    ('REPACKAGER', 'Repackager'),
    ('THRID_PARTY_LOGISTICS_PROVIDER', 'Third Party Logistics Provider'),
    ('TRADING_PARTNER_CONTACT_ADDRESS', 'Trading Partner Contact Address'),
    ('DISTRIBUTOR', 'Distributor')
]

TTRX_NOTIFICATION = [
    ('ALL', 'All transactions'),
    ('DAILY', 'On the first transaction of the day'),
    ('NONE', 'No notification')
]


class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = ["custom.connector.spt","res.partner"]
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'uuid':'uuid'}
    _TTRxToOdoo = {'uuid':'uuid'}

    # TTRx Fields
    uuid = fields.Char("UUID", readonly=True, copy=False, index=True)
    created_on = fields.Datetime('Create On', readonly=True, copy=False)
    last_update = fields.Datetime('Last Update', readonly=True, copy=False)
    gs1_id = fields.Char("GS1 ID")
    gs1_sgln = fields.Char("GS1 ID")
    type_ttr = fields.Selection(TTRX_TYPE, default="VENDOR", string='Type')
    customer_id = fields.Char("Customer ID")
    friendly_name = fields.Char("Trading Partner Friendly Name.")
    ttr_last_update = fields.Date('Last Update') #TODO: Excluir
    error_text = fields.Text(string="Log", track_visibility="onchange") #TODO: Excluir
    
    external_reference = fields.Char("External Reference")
    
    
    # Contacts #
    phone_ext = fields.Char("Phone Extension")
    new_trx_notification_type = fields.Selection(TTRX_NOTIFICATION, default="NONE", string='Frequency', help="On New \
                                                Transaction, the TP should be notified by Email on theses occurrences All, \
                                                daily or none")
    set_bool = fields.Boolean("bool") #TODO: Excluir
    
    # Flag Notification
    flag_notification_name = fields.Char("Flag Name")
    flag_notification_email = fields.Char("Flag Email")
    flag_notification_phone = fields.Char("Flag Phone")
    flag_notification_phone_ext = fields.Char("Flag Phone Extension")
    
    # Misc
    inbound_shipping_check_percentage = fields.Float("Inbound Shipment")
    outbound_shipping_check_percentage = fields.Float("Outbound Shipment")
    sender_id = fields.Char("Sender ID")
    receiver_id = fields.Char("Receiver ID")
    
    # Deletar
    url_config  = fields.Char("Sender ID")

    # Foreign Fields

    # Join Fields
    trading_partner_address_spt_ids = fields.One2many('trading.partner.address.spt', 'res_partner_id', 'Address')
    license_spt_ids = fields.One2many('license.spt', 'res_partner_id', 'License')

    # Odoo Fields
    tracktrace_is = fields.Boolean('Is TrackTraceRx2',compute="_compute_tracktrace", store=False)
    
    trading_partner_address_dft_id = fields.Many2one('trading.partner.address.spt', 'Main Address')

       
    def _compute_tracktrace(self):
        for reg in self:
            reg.tracktrace_is = bool(reg.uuid)

    def FromOdooToTTRx(self, values={}):
        var = {
            'uuid': values.get('uuid',self.uuid if bool(self.uuid) else None),
            'gs1_id': values.get('gs1_id',self.gs1_id),
            'gs1_sgln': values.get('gs1_id',self.gs1_sgln),
            'type': values.get('type_ttr',self.type_ttr),
            'customer_id': values.get('customer_id',self.customer_id),
            'name': values.get('name',self.name),
            'friendly_name': values.get('friendly_name',self.friendly_name),
            'external_reference': values.get('external_reference',self.external_reference),
            'phone': values.get('phone',self.phone), 
            'phone_ext': values.get('phone_ext',self.phone_ext),
            'notification_email': values.get('email',self.email),
            'external_reference': values.get('ref',self.ref),
            'new_trx_notification_type': values.get('new_trx_notification_type',self.new_trx_notification_type),
            'flag_notification_name': values.get('flag_notification_name',self.flag_notification_name),
            'flag_notification_email': values.get('flag_notification_email',self.flag_notification_email),
            'flag_notification_phone': values.get('flag_notification_phone',self.flag_notification_phone),
            'flag_notification_phone_ext': values.get('flag_notification_phone_ext',self.flag_notification_phone_ext),
            'inbound_shipping_check_percentage': values.get('inbound_shipping_check_percentage',\
                                                            self.inbound_shipping_check_percentage),
            'outbound_shipping_check_percentage': values.get('outbound_shipping_check_percentage',\
                                                             self.outbound_shipping_check_percentage),
            'sender_id': values.get('sender_id',self.sender_id),
            'receiver_id': values.get('receiver_id',self.receiver_id),
            'is_active': values.get('active',self.active),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
       
        var = {
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'gs1_id': values.get('gs1_id'),
            'gs1_sgln': values.get('gs1_id'),
            'type_ttr': values.get('type'),
            'customer_id': values.get('customer_id'),
            'name': values.get('name'),
            'friendly_name': values.get('friendly_name'),
            'external_reference': values.get('external_reference'),
            'phone': values.get('phone'), 
            'phone_ext': values.get('phone_ext'),
            'email': values.get('notification_email'),
            'ref': values.get('external_reference'),
            'new_trx_notification_type': values.get('new_trx_notification_type'),
            'flag_notification_name': values.get('flag_notification_name'),
            'flag_notification_email': values.get('flag_notification_email'),
            'flag_notification_phone': values.get('flag_notification_phone'),
            'flag_notification_phone_ext': values.get('flag_notification_phone_ext'),
            'inbound_shipping_check_percentage': values.get('inbound_shipping_check_percentage'),
            'outbound_shipping_check_percentage': values.get('outbound_shipping_check_percentage'),
            'sender_id': values.get('sender_id'),
            'receiver_id': values.get('receiver_id'),
            'is_active': values.get('active'),
        }
        CleanDataDict(var)
        return var

    @api.onchange('trading_partner_address_dft_id')
    def _onchange_address_main(self):
        if bool(self.trading_partner_address_dft_id):
            res_partners_list = self.env['res.partner'].search_read([('street', '=', self.trading_partner_address_dft_id.line1)])
            if bool(self.street == self.trading_partner_address_dft_id.line1):
                if len(res_partners_list) > 1:
                    test0 = res_partners_list[0]
                    test1 = res_partners_list[1]
                    self.EmailPhoneValidation()
                    result = super(res_partner, self).search([('id', '=', test1['id'])]).unlink()
                    result1 = self.env['res.partner'].search_read([('street', '=', self.trading_partner_address_dft_id.line1)])
                    return result
            else:    
                self.NameValidation()
                self.EmailPhoneValidation()
                self.AddressesValidation()

    def NameValidation(self):
        if bool(self.flag_notification_name):
            self.name = self.flag_notification_name
        else:
            return self.name

        if bool(self.trading_partner_address_dft_id.recipient_name):
            self.name = self.recipient_name
        else:
            return self.name

    def EmailPhoneValidation(self):
        if bool(self.trading_partner_address_dft_id.phone_ext): 
            self.phone = self.trading_partner_address_dft_id.phone + ' ext ' + self.trading_partner_address_dft_id.phone_ext 
        else:
            self.trading_partner_address_dft_id.phone = self.phone
                        
        if bool(self.trading_partner_address_dft_id.email):
            self.email = self.trading_partner_address_dft_id.email
        else:
            self.trading_partner_address_dft_id.email = self.email

    def AddressesValidation(self):
        self.street = self.trading_partner_address_dft_id.line1
        self.street2 = self.trading_partner_address_dft_id.line2
        self.city = self.trading_partner_address_dft_id.city
        self.zip = self.trading_partner_address_dft_id.zip
        self.state_id = self.trading_partner_address_dft_id.res_country_state_id
        self.country_id = self.trading_partner_address_dft_id.res_country_id

   
    @api.onchange('name')
    def _onchange_name(self):
        if not self.friendly_name:
            self.friendly_name = self.name
        self.flag_notification_name = self.name
   
    @api.onchange('email')
    def _onchange_email(self):
        self.flag_notification_email = self.email

    @api.onchange('phone')
    def _onchange_phone(self):
        self.flag_notification_phone = self.phone

    def BeforeCreateInOdoo(self, **params):
        if params['data'].get('type_ttr') in ['TRADING_PARTNER_CONTACT_ADDRESS']: 
            return False
        else:
            return True

    def BeforeWriteInOdoo(self, **params):
        if self.type_ttr in ['TRADING_PARTNER_CONTACT_ADDRESS']: 
            return False
        else:
            return True

    def BeforeUnlinkInOdoo(self, **params):
        if self.type_ttr in ['TRADING_PARTNER_CONTACT_ADDRESS']: 
            return False
        else:
            return True


    def AfterCreateFromTTRx(self, connector, response, data):
        self.CreateUpdateModelsFromTTRx(connector=connector, response=response, data=data)
        return True

    def AfterWriteFromTTRx(self, connector, response, data):
        self.CreateUpdateModelsFromTTRx(connector=connector, response=response, data=data)
        return True

    def CreateUpdateModelsFromTTRx(self, connector, response, data):
        if bool(self):
            addresses = self.env['trading.partner.address.spt'].SyncFromTTRx(connector,partner_uuid=self.uuid,primary_model='partner')
            self.env['trading.partner.users.spt'].SyncFromTTRx(connector,partner_uuid=self.uuid)
            self.env['license.spt'].SyncFromTTRx(connector,partner_uuid=self.uuid,primary_model='partner')
            context = dict(self.env.context or {})
            context['no_rewrite'] = True
            if len(addresses) > 0:
                if bool(response.get('default_billing_address_uuid')):
                    billing = self.env['trading.partner.address.spt'].search([('uuid','=',response['default_billing_address_uuid'])],limit=1)
                    if not bool(billing):
                        billing = self.with_context(context).trading_partner_address_spt_ids[0]
                    else:
                        billing.res_partner_id.with_context(context).type = 'invoice'
                    if bool(billing):
                        self.with_context(context).trading_partner_address_dft_id = billing 
                        self.with_context(context)._onchange_address_main()
                if bool(response.get('default_shipping_address_uuid')):
                    shipping = self.env['trading.partner.address.spt'].search([('uuid','=',response['default_shipping_address_uuid'])],limit=1)
                    if bool(shipping):
                        billing.res_partner_id.with_context(context).type = 'delivery'
        return True
