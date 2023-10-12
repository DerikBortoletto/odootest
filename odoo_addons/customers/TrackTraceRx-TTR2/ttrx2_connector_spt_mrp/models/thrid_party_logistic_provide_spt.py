from odoo import models, fields, api
from ..tools import DateTimeToOdoo, CleanDataDict, CleanDataList





class thrid_party_logistic_provide_spt(models.Model):
    _name = 'thrid.party.logistic.provide.spt'
    _inherit = "custom.connector.spt"
    _description = 'Thrid Party Logistic Provide'
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'uuid': 'uuid'}
    _TTRxToOdoo = {'uuid': 'uuid'}
    
    uuid = fields.Char('UUID', readonly=True, copy=False, index=True)
    created_on = fields.Datetime('Create On', readonly=True, copy=False)
    last_update = fields.Datetime('Create On', readonly=True, copy=False)
    name = fields.Char('Name', required=True)
        
    products_scope = fields.Selection([('ALL_PRODUCTS', 'All products is handled by the 3PL'),
                                       ('SELECTED', 'Only the selected products is handled by the 3PL')], string='Products Scope')
    automatic_transfer = fields.Boolean('Automatic Transfer', help='When possible, initiate automatically inventory transfer to \
                                        3PL on Inbound Shipment if the shipment destination is not the 3PL location.')
    disable_epcis = fields.Boolean('Disable EPCIS for this 3PL. (Not recommanded)')
    
    inbound_action = fields.Selection([('SEND_A_COPY', 'Send a copy to the 3PL'),
                                       ('DO_NOTHING', 'Do nothing')], string='Action to do', help="Action to do when an inbound \
                                       EPCIS message is received and where it's destination is the 3PL.")
    inbound_3pl = fields.Selection([('PROCESS_UNLESS_PO_MATCH', 'Process it and create transaction, unless the PO # match'),
                                    ('PROCESS_REGARDLESS_PO_MATCH', 'Process it and create transaction ignore if an existing PO # match'),
                                    ('DO_NOTHING', 'Do nothing')], string='If the data came from the 3PL')
    shipment_action = fields.Selection([('SEND_A_COPY', 'Send a copy to the 3PL'),
                                        ('DO_NOTHING', 'Do nothing')], string='Ship Action to do', help='Actions to do when an \
                                        outbound shipment is created in TrackTrace.')
    sales_order_exist = fields.Selection([('VALIDATE_ONLY', 'Validate the content only (trigger error on mismatch)'),
                                          ('UPDATE_SALE_ORDER', 'Update the sale order')], string='If the Sales Order exist')
    shipment_exist = fields.Selection([('VALIDATE_ONLY', 'Validate the content only (trigger error on mismatch)'),
                                       ('UPDATE_SHIPMENT', 'Update the shipment')], string='If the Shipment exist')
    sales_order_not_exist = fields.Selection([('CREATE_SALES_ORDER', 'Create a Sales Orde'),
                                              ('TRIGGER_ERROR', 'Trigger an Error')], string='If the Sales Order does not exist')
    shipment_not_exist = fields.Selection([('CREATE_SHIPMENT', 'Create a shipment'),
                                           ('TRIGGER_ERROR', 'Trigger an Error')], string='If the Shipment does not exist')

    sender_id = fields.Char(string='Sender ID',help="Sender ID for X12 EDI communication.")
    receiver_id = fields.Char(string='Receiver ID',help="Override Receiver ID for X12 EDI communication. Optionnal. \
                                                         Null/empty will use the company default.")
    as2_id = fields.Char(string="AS2ID")

    outbound_epcis_generator = fields.Selection([('DEFAULT', 'Default'),
                                                 ('TRACELINK', 'Trace Link'),
                                                 ('RFXCEL','RFXCEL'),
                                                 ('ABC1.2','ABC 1.2'),
                                                 ('CARDINAL','Cardinal')], 
                                                string='Outbound EPCIS Generator Type', default='DEFAULT')
    
    communication_format = fields.Selection([('EPCIS', 'EPCIS'),
                                             ('X12', 'X12'),
                                             ('WOODFIELD','Woodfield Tabulated')], 
                                             string='Outbound EPCIS Generator Type', defualt="EPCIS") 
    
    # Local Fields
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, 
                                 default=lambda self: self.env.user.company_id)
    connector_id = fields.Many2one('connector.spt', 'Connector')

    product_category_ids = fields.Many2many('product.category', 'product_category_3pl_provide', string='Product Category')
    product_spt_ids = fields.Many2many('product.spt', 'product_spt_3pl_provide', string='Products')
    location_spt_ids = fields.Many2many('locations.management.spt', string='Locations')

    # Post
    def FromOdooToTTRx(self, values={}):
        products_categories = []
        if bool(values.get('product_category_ids')):
            for categ in values['product_category_ids']:
                products_categories.append(self.env['product.category'].browse(categ).tt_id or None)
        else:
            for categ in self.products_categories:
                products_categories.append(categ.tt_id or None)
        CleanDataList(products_categories)
        products = []
        if bool(values.get('product_spt_ids')):
            for prod in values['product_spt_ids']:
                products.append(self.env['product.spt'].browse(prod).uuid or None)
        else:
            for prod in self.product_spt_ids:
                products.append(prod.uuid or None)
        CleanDataList(products)
        locations = []
        if bool(values.get('location_spt_ids')):
            for loca in values['location_spt_ids']:
                locations.append(self.env['locations.management.spt'].browse(loca)._OdooToTTRx() or None)
        else:
            for loca in self.location_spt_ids:
                locations.append(loca._OdooToTTRx() or None)
        CleanDataList(locations)

        var = {
            'uuid_3pl': values.get('uuid',self.uuid if bool(self.uuid) else None),
            'name': values.get('name',self.name),
            'products_scope': values.get('products_scope',self.products_scope),
            'is_automatic_transfer_enabled': values.get('automatic_transfer',self.automatic_transfer),
            'is_epcis_disabled': values.get('disable_epcis',self.disable_epcis or None if not bool(values) else None),
            'received_inbound_for_3pl_action_to_do': values.get('inbound_action',self.inbound_action or None if not bool(values) else None),
            'received_inbound_from_3pl_transaction_action_to_do': values.get('inbound_3pl',self.inbound_3pl or None if not bool(values) else None),
            'outbound_shipment_created_in_tt_action_to_do': values.get('shipment_action',self.shipment_action or None if not bool(values) else None),
            'outbound_shipment_received_from_3pl_action_to_do_sales_order_exists': values.get('sales_order_exist',
                                                                                              self.sales_order_exist or None if not bool(values) else None),
            'outbound_shipment_received_from_3pl_action_to_do_shipment_exists': values.get('shipment_exist',self.shipment_exist or None if not bool(values) else None),
            'outbound_shipment_received_from_3pl_action_to_do_sales_order_not_exists': values.get('sales_order_not_exist',
                                                                                                  self.sales_order_not_exist or None if not bool(values) else None),
            'outbound_shipment_received_from_3pl_action_to_do_shipment_not_exists': values.get('shipment_not_exist',
                                                                                               self.shipment_not_exist or None if not bool(values) else None),
            'products_categories': products_categories,
            'products': products,
            'locations': locations,
            'sender_id': values.get('sender_id',self.sender_id or None if not bool(values) else None),
            'receiver_id': values.get('receiver_id',self.receiver_id or None if not bool(values) else None),
            'as2_id': values.get('as2_id',self.as2_id or None if not bool(values) else None),
            'outbound_epcis_generator_type': values.get('outbound_epcis_generator',self.outbound_epcis_generator or None if not bool(values) else None),
            'communication_format': values.get('communication_format',self.communication_format or None if not bool(values) else None),
        }
        CleanDataDict(var)
        return var

    # Get
    def FromTTRxToOdoo(self, values):
        var = {
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': values.get('name'),
            'products_scope': values.get('products_scope'),
            'automatic_transfer': values.get('is_automatic_transfer_enabled'),
            'disable_epcis': values.get('is_epcis_disabled'),
            'inbound_action': values.get('received_inbound_for_3pl_action_to_do'),
            'inbound_3pl': values.get('received_inbound_from_3pl_transaction_action_to_do'),
            'shipment_action': values.get('outbound_shipment_created_in_tt_action_to_do'),
            'sales_order_exist': values.get('outbound_shipment_received_from_3pl_action_to_do_sales_order_exists'),
            'shipment_exist': values.get('outbound_shipment_received_from_3pl_action_to_do_shipment_exists'),
            'sales_order_not_exist': values.get('outbound_shipment_received_from_3pl_action_to_do_sales_order_not_exists'),
            'shipment_not_exist': values.get('outbound_shipment_received_from_3pl_action_to_do_shipment_not_exists'),
            'product_category_ids': None, # products_categories,
            'product_spt_ids': None, # products,
            'location_spt_ids': None, #locations,
            'sender_id': values.get('sender_id'),
            'receiver_id': values.get('receiver_id'),
            'as2_id': values.get('as2_id'),
            'outbound_epcis_generator': values.get('outbound_epcis_generator_type'),
            'communication_format': values.get('communication_format'),
        }
        CleanDataDict(var)
        return var

    def BeforeCreateFromTTRx(self, connector, response, data):
        ttr_categs = [x['id'] for x in response['products_categories']] if bool(response.get('products_categories')) else []
        ttr_produs = [x['uuid'] for x in response['products']] if bool(response.get('products')) else []
        ttr_locats = [x['uuid'] for x in response['locations']] if bool(response.get('locations')) else []

        categ_ids = []
        for ttr_categ in ttr_categs:
            categ_ids += [self.env['product.category'].SyncFromTTRx(connector,id=ttr_categ).id]
        data['product_category_ids'] = [(6,0, categ_ids)] if bool(categ_ids) else [(5,)]

        prod_ids = []
        for ttr_produ in ttr_produs:
            prod_ids += [self.env['product.spt'].SyncFromTTRx(connector,uuid=ttr_produ).id]
        data['product_spt_ids'] = [(6,0, prod_ids)] if bool(prod_ids) else [(5,)]

        loc_ids = []
        for ttr_locat in ttr_locats:
            loc_ids += [self.env['locations.management.spt'].SyncFromTTRx(connector,uuid=ttr_locat).id]
        data['location_spt_ids'] = [(6,0, loc_ids)] if bool(loc_ids) else [(5,)]
        
        return True


