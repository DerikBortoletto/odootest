import json
import logging
from itertools import groupby
from time import sleep

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_compare
from ..tools import DateTimeToOdoo, CleanDataDict
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

_logger = logging.getLogger(__name__)

STATES = {'done': [('readonly', True)], 'cancel': [('readonly', True)]}

class stock_picking(models.Model):
    _name = 'stock.picking'
    _inherit = ["custom.connector.spt","stock.picking"]
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'incoming': {'uuid':'uuid'},
                   'outgoing': {'uuid':'uuid'}}
    _TTRxToOdoo = {'uuid':'uuid'}

    def _can_send_to_ttr2(self):
        res = False
        if not self.no_send_to_ttr2:
            res = super()._can_send_to_ttr2()
            if res:
                itens = self.move_lines.filtered(lambda x: bool(x.product_id.product_spt_id.uuid) == True)
                if self.picking_type_id.code == 'incoming': # eNTRADA
                    uuid_order_in_ttx = bool(self.purchase_id.uuid)
                elif self.picking_type_id.code == 'outgoing':
                    uuid_order_in_ttx = bool(self.sale_id.uuid)
                else:
                    uuid_order_in_ttx = False
                if uuid_order_in_ttx:
                    if not bool(self.uuid) and self.state not in ['done','cancel']:
                        if len(itens) > 0:
                            if self.picking_type_id.code == 'incoming' and bool(self.storage_spt_id):
                                res = True
                            elif self.picking_type_id.code == 'outgoing' and bool(self.storage_spt_id):
                                res = True
                    else:
                        res = True
        return res

    @api.depends('move_lines','uuid','state','location_spt_id','storage_spt_id','shelf_spt_id')
    def compute_can_send_to_ttr2(self):
        for reg in self:
            reg.can_send_to_ttr2 = reg._can_send_to_ttr2()

    # def can_send_ttrx(self):
    #     can_send_ttr2 = len(self.move_lines.filtered(lambda x: bool(x.product_id.product_spt_id.uuid) == True)) > 0
    #     if can_send_ttr2:
    #         if self.picking_type_id.code == 'incoming': # eNTRADA
    #             can_send_ttr2 = bool(self.purchase_id.uuid)
    #         elif self.picking_type_id.code == 'outgoing':
    #             can_send_ttr2 = bool(self.sale_id.uuid)
    #         else:
    #             can_send_ttr2 = False
    #         if can_send_ttr2:
    #             if self.state in ['done','cancel']:
    #                 can_send_ttr2 = False
    #     return can_send_ttr2

    @api.depends('shipment_picking_uuid','shipment_picking_ids')
    def _compute_is_picked(self):
        for reg in self:
            if len(reg.shipment_picking_ids) > 0:
                reg.is_picked = True
                reg.is_picked_closed = reg.shipment_picking_ids[0].is_session_closed
            else:
                reg.is_picked = False

    @api.depends()
    def _compute_ttrx_state(self):
        self.ttrx_state = 'UNKNOWN'
        if self.uuid:
            if self.is_void:
                self.ttrx_state = 'CANCELLED'
            else:
                if self.picking_type_code == 'incoming':
                    if not self.is_received and not self.is_verified:
                        self.ttrx_state = 'SHIPPED'
                    elif self.is_received and not self.is_verified:
                        self.ttrx_state = 'RECEIVED'
                    elif self.is_received and self.is_verified:
                        self.ttrx_state = 'VERIFIED'
                elif self.picking_type_code == 'outgoing':
                    if self.is_approved and not self.is_picked and not self.is_picked_closed and not self.is_shipped:
                        self.ttrx_state = 'APPROVED'
                    elif self.is_approved and self.is_picked and not self.is_picked_closed and not self.is_shipped:
                        self.ttrx_state = 'PICKED'
                    elif self.is_approved and self.is_picked and self.is_picked_closed and not self.is_shipped:
                        self.ttrx_state = 'PICKED_CLOSED'
                    elif self.is_approved and self.is_picked and self.is_picked_closed and self.is_shipped:
                        self.ttrx_state = 'SHIPPED'

    def _domain_storage_spt(self):
        active_id = batch_id = self.env.context.get('active_id')
        reg = self.browse([active_id])
        location_id = reg.location_spt_id.stock_location_id.id
        return [('location_id', '=', location_id)]

    def _auto_data_sync(self):
        connector = self.env['connector.spt'].search([('company_id','=',self.env.user.company_id.id)],limit=1)
        if bool(connector):
            return not connector.auto_data_sync
        else:
            return True
    
    uuid = fields.Char('UUID', copy=False, states=STATES)
    queue_uuid = fields.Char('Queue UUID',copy=False, states=STATES)    
    queue_url = fields.Char('Queue URL',copy=False, states=STATES)    
    created_on = fields.Datetime('Create On', readonly=True)
    last_update = fields.Datetime('Last Update',readonly=True)
    po_nbr = fields.Char('PO Number', states=STATES)
    internal_reference_number = fields.Char('Internal Reference Nbr', states=STATES)
    release_nbr = fields.Char('Release Number', states=STATES)
    transaction_date = fields.Date('Order Date', states=STATES)
    billing_address = fields.Many2one('trading.partner.address.spt', 'Bought By', states=STATES)
    ship_from_address = fields.Many2one('trading.partner.address.spt', 'Ship From', states=STATES)
    ship_to_address = fields.Many2one('trading.partner.address.spt', 'Ship To', states=STATES)
    sold_by_address = fields.Many2one('trading.partner.address.spt', 'Sold By', states=STATES)
    po_transaction_uuid = fields.Char("Transaction UUID", states=STATES)
    check_shipment = fields.Boolean(compute='_compute_shipment_type')
    location_dest_id = fields.Many2one('stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        readonly=False, required=True, states=STATES)
    location_id = fields.Many2one('stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        readonly=False, required=True, states=STATES)
    location_spt_id = fields.Many2one('locations.management.spt', 'Location TTRx', states=STATES)
    storage_spt_id = fields.Many2one('storage.areas.spt', string="Storage TTRx", domain="[('stock_location_id','=',location_id)]", states=STATES)
    storage_id = fields.Many2one('stock.location', string="Location", compute="_get_locations", store=False)
    shelf_spt_id = fields.Many2one('shelf.spt', string="Source Shelf", domain="[('stock_location_id','=',storage_id)]",states=STATES)
    queue_id = fields.Many2one('queue.spt', "Queue Thread", readonly=False, states=STATES)
    container_serial = fields.Many2one('container.spt',string='Container Serial')
    shipment_picking_uuid = fields.Char('Picking uuid', states=STATES)
    shipment_picking_ids = fields.One2many('picking.spt', 'stock_picking_id', string='Pickings')
    is_approved = fields.Boolean('Approved',default=False)
    is_picked = fields.Boolean('Picked', compute='_compute_is_picked', store=True) # Separada
    is_picked_closed = fields.Boolean('Picked and closed', compute='_compute_is_picked', store=True) # Separada
    is_shipped = fields.Boolean('Shipped',default=False) # Enviado
    is_verified = fields.Boolean('Verified',default=False) # Enviado
    is_received = fields.Boolean('Received',default=False) 
    is_void = fields.Boolean('Void')  # Quando a entrega estiver cancelada..
    
    ttrx_state = fields.Char(compute="_compute_ttrx_state", store=False)

    # send_to_ttr2 = fields.Boolean('Send to TTRx', default=False)
    # can_send_ttr2 = fields.Boolean('Auto Send to TTRx', compute="_can_to_send_ttrx", store=False, readonly=True)
    no_send_to_ttr2 = fields.Boolean('No Send to TTRx', default=lambda self: self._auto_data_sync(),copy=False)
    can_send_to_ttr2 = fields.Boolean('Can Send to TTRx', compute="compute_can_send_to_ttr2", store=False, readonly=True)

    @api.depends('location_spt_id')
    def _get_locations(self):
        self.storage_id = self.storage_spt_id.stock_location_id
        
    @api.onchange('location_spt_id')
    def onchange_location_spt_id(self):
        if self.picking_type_id.code == 'incoming':
            if bool(self.location_spt_id):
                self.location_dest_id = self.location_spt_id.stock_location_id
            else:
                self.location_dest_id = False
        elif self.picking_type_id.code == 'outgoing':
            if bool(self.location_spt_id):
                self.location_id = self.location_spt_id.stock_location_id
            else:
                self.location_id = False
        self.storage_spt_id = False
        self.shelf_spt_id = False
        location_id = self.location_spt_id.stock_location_id or self.env['stock.location']
        domain = {'storage_spt_id': [('location_id', '=', location_id.id)], 'shelf_spt_id': [('location_id', '=', False)]}
        return {'domain': domain}

    @api.onchange('storage_spt_id')
    def onchange_storage_spt_id(self):
        if self.picking_type_id.code == 'incoming':
            if bool(self.storage_spt_id):
                self.location_dest_id = self.storage_spt_id.stock_location_id
            else:
                self.location_dest_id = False
        elif self.picking_type_id.code == 'outgoing':
            if bool(self.storage_spt_id):
                self.location_id = self.storage_spt_id.stock_location_id
            else:
                self.location_id = False
        self.shelf_spt_id = False
        val_id = self.storage_spt_id.stock_location_id.id or False
        domain = {'shelf_spt_id': [('location_id', '=', val_id)]}
        return {'domain': domain}

    @api.onchange('shelf_spt_id')
    def onchange_shelf_spt_id(self):
        if self.picking_type_id.code == 'incoming':
            if bool(self.shelf_spt_id):
                self.location_dest_id = self.shelf_spt_id.stock_location_id
            else:
                self.location_dest_id = False
        elif self.picking_type_id.code == 'outgoing':
            if bool(self.shelf_spt_id):
                self.location_id = self.shelf_spt_id.stock_location_id
            else:
                self.location_id = False
   
    @api.onchange('queue_uuid')
    def onchange_queue_uuid(self):
        if bool(self.queue_uuid):
            self.queue_id = self.env['queue.spt'].SyncFromTTRx(self.connector_id,uuid=self.queue_uuid,ForceUpdate=True)
        else:
            self.queue_id = False
    
    @api.depends('picking_type_id')
    def _compute_shipment_type(self):
        _logger.debug("DEBUG 79: Entrou no _compute_shipment_type")
        for rec in self:
            if rec.picking_type_id.code == 'incoming':
                rec.check_shipment = True
            else:
                rec.check_shipment = False
 
    def FromOdooToTTRx(self, connector, values={}):
        var = super().FromOdooToTTRx(connector=connector,values=values)
        uuid = values.get('uuid', self.uuid if bool(self.uuid) else None)
        if self.picking_type_id.code == 'outgoing':
            request_vals_shipment = self.prepare_vals_for_outbound_shipment()
            var.update(request_vals_shipment)
        elif self.picking_type_id.code == 'incoming':
            request_vals_shipment = self.prepare_vals_for_incoming_shipment()
            var.update(request_vals_shipment)
        var.update({
            'uuid': uuid,
            'shipment_date': values.get('create_date', str(self.create_date))[0:10] or None,
            'estimated_delivery_date': values.get('scheduled_date', str(self.scheduled_date))[0:10] or None,
            'shipping_carrier_uuid': None,
            'custom_shipping_carrier': None,
            'shipping_method_uuid': None,
            'custom_shipping_method': None,
            'tracking_number': None,
            'tracking_link': None,
            'notes': values.get('note', self.note or None),
            'is_create_transaction_from_shipment_data': None,
            'transaction_date': None,
            'new_shipment_status': None,
            'new_shipment_received_and_validated_storage_area_uuid': None,
            'new_shipment_received_and_validated_storage_shelf_uuid': None,
        })
        CleanDataDict(var)
        return var
    
    def FromTTRxToOdoo(self, connector, values):
        # self.ensure_one()
        var = super().FromTTRxToOdoo(connector=connector,values=values)
        regexist = False
        readonly = False
        regstate = ''
        if values.get('uuid'):
            pickings = self.search([('uuid','=',values['uuid']),('state','!=','cancel')])
            regexist = bool(pickings)
            if regexist:
                regstate = pickings[0].state
                readonly = pickings[0].state in ['done','cancel']
            #TODO: Verificar se picking está validado, se estiver não pode atualizar...
            
        transactions = values.get('transactions',[])
        warehouse = connector.wharehouse_id
        partner_id = values.get('trading_partner') and values['trading_partner'].get('uuid') and \
                     self.env['res.partner'].SyncFromTTRx(connector,uuid=values['trading_partner']['uuid'])

        source = []
        transaction_uuid = ''
        for transaction in transactions:
            if bool(transaction['po_number']):
                source += [transaction['po_number']]
            transaction_uuid = transaction['uuid']

        sale_id = self.env['sale.order']
        purchase_id = self.env['purchase.order']
        location_id = self.env['stock.location']
        location_dest_id = self.env['stock.location']
        location_spt_id = self.env['locations.management.spt']
        storage_spt_id = self.env['storage.areas.spt']
        shelf_spt_id = self.env['shelf.spt']

        
        # move_lines = []

        delivery_status = values.get('delivery_status')
        is_approved = False
        is_shipped = False
        is_verified = False
        is_received = False
        is_picked_closed = False
        is_void = values.get('is_void', False)

        if values['type'] == 'Inbound':
            purchase_data = self._GetRecord(connector, 'purchase.order', uuid=transaction_uuid) if bool(transaction_uuid) else dict()
            received_data = self._GetRecord(connector, 'stock.picking.receiving', uuid=values['uuid'])
            purchase_id = self.env['purchase.order'].search([('uuid','=',transaction_uuid)],limit=1)
            location_uuid = False
            storage_uuid = False
            shelf_uuid = False
            if bool(received_data):
                location_uuid = received_data.get('location_uuid', False) 
                storage_uuid = received_data['received_storage_area']['uuid'] if received_data.get('received_storage_area') else False
                shelf_uuid = received_data['received_storage_shelf']['uuid'] if received_data.get('received_storage_shelf') else False
            if not bool(location_uuid):
                location_uuid = purchase_data.get('location_uuid', False)
            picking_type_id = warehouse.in_type_id
            location_id = self.env['stock.location'].search([('usage','=','supplier')],limit=1)

            if bool(location_uuid):
                location_spt_id = self.env['locations.management.spt'].SyncFromTTRx(connector,uuid=location_uuid)
            if bool(storage_uuid):
                storage_spt_id = self.env['storage.areas.spt'].SyncFromTTRx(connector,uuid=storage_uuid)
            if bool(shelf_uuid):
                shelf_spt_id = self.env['shelf.spt'].SyncFromTTRx(connector,uuid=shelf_uuid)

            if bool(shelf_spt_id):
                location_dest_id = shelf_spt_id.stock_location_id
            elif bool(storage_spt_id):
                location_dest_id = storage_spt_id.stock_location_id
            elif bool(location_spt_id):
                location_dest_id = location_spt_id.stock_location_id

            if not bool(location_dest_id):
                location_dest_id = self.env['purchase.order'].search([('uuid','=',transaction_uuid)],limit=1).location_spt_id.stock_location_id
            if not bool(location_dest_id):
                location_dest_id = picking_type_id.default_location_dest_id
                location_spt_id = location_dest_id.location_spt_id

            is_shipped = delivery_status in ['SHIPPED','RECEIVED']
            is_received = delivery_status == 'SHIPPED' and values.get('is_received',False) or delivery_status == 'RECEIVED'
            is_verified = delivery_status == 'RECEIVED'
            
        elif values['type'] == 'Outbound':
            sale_data = self._GetRecord(connector, 'sale.order', uuid=transaction_uuid) if bool(transaction_uuid) else dict()
            sale_id = self.env['sale.order'].search([('uuid','=',transaction_uuid)],limit=1)
            location_uuid = sale_data.get('location_uuid', False) 
            storage_uuid = False
            shelf_uuid = False

            picking_type_id = warehouse.out_type_id
            if bool(location_uuid):
                location_spt_id = self.env['locations.management.spt'].SyncFromTTRx(connector,uuid=location_uuid)
                location_id = location_spt_id.stock_location_id
            if not bool(location_id):
                location_id = self.env['sale.order'].source_location
                location_spt_id = location_id.location_spt_id
            if not bool(location_id):
                location_id = picking_type_id.default_location_id
                location_spt_id = location_id.location_spt_id
            location_dest_id = self.env['stock.location'].search([('usage','=','customer')],limit=1)
            is_approved = values.get('is_approved',False)
            is_shipped = delivery_status == 'SHIPPED'

        
        var.update({
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'picking_type_id': picking_type_id.id or None,
            'location_dest_id': location_dest_id.id or None,
            'location_id': location_id.id or None,
            'location_spt_id': location_spt_id.id or None,
            'storage_spt_id': storage_spt_id.id or None,
            'shelf_spt_id': shelf_spt_id.id or None,
            'partner_id': partner_id.id or None,
            'origin': ','.join(source),
            'scheduled_date': fields.Datetime.now(),
            # 'move_ids_without_package': move_lines or None,
            'sale_id': sale_id.id or None,
            'purchase_id': purchase_id.id or None,
            # 'state': 'confirmed',
            'is_approved': is_approved,
            'is_shipped': is_shipped,
            'is_verified': is_verified,
            'is_received': is_received,
            'is_picked_closed': is_picked_closed,
            'is_void': is_void,
        })
        CleanDataDict(var)
        return var

    def _CreateUpdateFromTTRx(self, connector, **params):
        """
            submodal
            primarykey
        """
        connector.logger_info('CREATEUPDATE', message='try create/update a registry from TTRx data in Odoo %s' % str(params), model=self._name, res_id=self.id)
        context = dict(self.env.context or {})
        NoCreate = bool(context.get('NoCreate',False))
        NoUpdate = bool(context.get('NoUpdate',False))
        response, data = self.GetValuesInTTRx(connector, **params)
        exist = self.env[self._name]
        if bool(response) and not bool(response.get('error')):
            domain = self._GetTTRxDomainToSearch(data)
            exist = self.search(domain, limit=1)
            if not bool(exist) and bool(data.get('picking_type_id',False)):
                pickings = False
                picking_type_id = self.env['stock.picking.type'].browse(data['picking_type_id'])
                if picking_type_id.code == 'outgoing' and bool(data.get('sale_id',False)):
                    pickings = self.env['sale.order'].browse(data['sale_id']).picking_ids.filtered(lambda x: not bool(x.uuid) and x.state in ['draft','confirmed','assigned'])
                elif picking_type_id.code == 'incoming' and bool(data.get('purchase_id',False)):
                    pickings = self.env['purchase.order'].browse(data['purchase_id']).picking_ids.filtered(lambda x: not bool(x.uuid) and x.state in ['draft','confirmed','assigned'])
                if bool(pickings):
                    exist = pickings[0]
                    # exist.move_line_ids.unlink()
                    # exist.move_lines.unlink()
            res = exist.BeforeCreateFromTTRx(connector, response, data)
            if bool(res):
                if bool(exist):
                    if not NoUpdate:
                        if bool(data.get('picking_type_id',False)):
                            data.pop('picking_type_id')
                        context = dict(self.env.context or {})
                        context['no_rewrite'] = True
                        exist.with_context(context)._clear_moves_line()
                        exist.with_context(context).write(data)
                else:
                    if not NoCreate:
                        exist = self.create(data)
            exist.AfterCreateFromTTRx(connector,response,data)
            exist._cr.commit()
        elif bool(response) and bool(response.get('error',False)):
            connector.logger_error('CREATEUPDATE', message=str(response.get('error','')), model=self._name, res_id=self.id)
            if not self.env.context.get('NotRaiseError',False):
                raise UserError(response['error'])
        return exist

    def AfterCreateFromTTRx(self, connector, response, data):
        context = dict(self.env.context or {})
        context['no_rewrite'] = True
        
        move = self.env['stock.move']
        line_move = self.env['stock.move.line']
        
        if self.picking_type_id.code == 'outgoing':
            if self.is_approved:
                pickings = self._get_pickings()
                
                if len(pickings) == 0:
                    self.with_context(context).write({
                        'is_picked': False,
                        'is_picked_closed': False,
                    })
                else:
                    for picking in pickings:
                        if picking.status == 'PICKING_IN_PROGRESS':
                            self.with_context(context).write({
                                'is_picked': True,
                                'is_picked_closed': False,
                            })
                        elif picking.status == 'PICKING_COMPLETED':
                            self.with_context(context).write({
                                'is_picked': True,
                                'is_picked_closed': True,
                            })

            self._cr.commit()
            
            # Cria/Altera as linhas de movimento
            for lineItem in response['ShipmentLineItem']:
                move_id = move.CreateUpdateFromTTRx(connector, self, lineItem)

            if self.state == 'draft' and self.is_approved:
                self.action_confirm()
            
            if self.state == 'confirmed':
                for lineItem in response['ShipmentLineItem']:
                    move_id = move.search([('uuid','=',lineItem['uuid'])])
                    if bool(move_id):
                        if move_id.state == 'confirmed' and self.is_picked_closed:
                            move_id.state = 'assigned'
                        if move_id.state == 'assigned':
                            line_move_ids = line_move.CreateUpdateFromTTRx(connector, self, move_id, lineItem['details'])
                            if bool(line_move_ids):
                                if move_id.product_id.tracking == 'serial':
                                    for line_move in line_move_ids:
                                        line_move.write({
                                            'qty_done': move_id.product_uom_qty,
                                            'product_uom_qty': move_id.product_uom_qty,
                                        })
                                else:
                                    line_move_ids[0].write({
                                        'qty_done': move_id.product_uom_qty,
                                        'product_uom_qty': move_id.product_uom_qty,
                                    })
                                    self.state = 'assigned'
            if self.state == 'assigned':
                self.button_validate()

        elif self.picking_type_id.code == 'incoming':
            # Cria/Altera as linhas de movimento
            for lineItem in response['ShipmentLineItem']:
                move_id = move.CreateUpdateFromTTRx(connector, self, lineItem)
            
            if self.state == 'draft':
                self.state = 'assigned'
            
            if self.is_received:
                for lineItem in response['ShipmentLineItem']:
                    move_id = move.search([('uuid','=',lineItem['uuid'])])
                    if bool(move_id):
                        if move_id.state not in ['cancel','done']:
                            line_move_ids = line_move.CreateUpdateFromTTRx(connector, self, move_id, lineItem['details'])
                        if move_id.state == 'draft':
                            move_id.state = 'confirmed'
                        if move_id.state == 'confirmed' and self.is_received:
                            move_id.state = 'assigned'
                
            if self.is_verified and self.state == 'assigned':
                self.button_validate()
            
        return True

    def _get_pickings(self):
        res = self.env['picking.spt']
        
        picking_uuids = set()
        pickings = self._GetList(self.connector_id, 'picking.spt', queries={'shipment_uuid': self.uuid})
        if bool(pickings):
            for picking in pickings:
                if bool(picking.get('uuid', False)):
                    picking_uuids.add(picking.get('uuid', False))
                    res += self.env['picking.spt'].SyncFromTTRx(self.connector_id,uuid=picking['uuid'],ForceUpdate=True)

        picking_ids = res.search([('stock_picking_id','=',self.id)])
        unlink_ids = set()
        for picking_id in picking_ids:
            if bool(picking_id.uuid):
                if not picking_id.uuid in picking_uuids:
                    unlink_ids.add(picking_id.id)
            else:
                unlink_ids.add(picking_id.id)
        if bool(unlink_ids):
            self.env['picking.spt'].browse(unlink_ids).unlink()
        return res

    def _lot_serial(self, value):
        x = str(value).find('/')
        if x >= 2:
            lote = value[:((x-1)*(-1))]
            serial = value[(x+1):]
        else:
            lote = value
            serial = ''
        return lote, serial

    def prepare_vals_for_incoming_shipment(self):
        """
        Prepared vals for inbound shipment ttr2
        :return:
        """
        _logger.debug("DEBUG 214: Entrou no prepare_vals_for_incoming_shipment")

        aggregation_data = {}

        if self.container_serial:
            aggregation_data.update({
                "type": "container",
                "serial": self.container_serial.name
            })
        
        item_lines = []
        content = []
        for move in self.move_lines:
            if move.quantity_done >= 1:
                details = []
                for move_line in move.move_line_nosuggest_ids:
                    qty_in = int(move_line.qty_done or move_line.product_uom_qty)
                    tracking = move_line.product_id.tracking
                    if qty_in >= 1:
                        lot_id = move_line.lot_id
                        if bool(lot_id):
                            lote, serial = self._lot_serial(lot_id.name)
                        else:
                            lote = move_line.lot_name
                            serial = ''
                        # sdi = '%s%s' % (lote,str(move.id).zfill(4)) 
                        sdi = '%s' % (str(move.id).zfill(4))  
                        # Valor do Content
                        if tracking == 'lot':
                            content_vals = {
                                "product_name": move_line.product_id.name,
                                "type": "product",
                                "lot_or_source": lote,
                                "sdi": sdi,
                                "lot_based_quantity": qty_in
                            }
                        elif tracking == 'serial':
                            content_vals = {
                                "product_name": move_line.product_id.name,
                                "type": "product",
                                "lot_or_source": lote,
                                "serial": serial,
                                "sdi": sdi} 
                        CleanDataDict(content_vals)
                        content.append(content_vals)  
                        # Valor dos detalhes                     
                        details_vals = {
                            "product_name": move_line.product_id.name,
                            "quantity": int(qty_in),
                            "lot_number":  lote,
                            "lot_type": "LOT_BASED" if tracking == 'lot' else "SERIAL_BASED",
                            "sdi": sdi,
                            # "history": [],
                            # "attachments": [],
                        }
                        if bool(lot_id) and hasattr(lot_id, 'life_date'):
                            details_vals.update({
                                "expiration_date": str(lot_id.life_date.date()) if bool(lot_id.life_date) else None,
                                "production_date": str(lot_id.production_date.date()) if bool(lot_id.production_date) else None,
                                "best_by_date": str(lot_id.use_date.date()) if bool(lot_id.use_date) else None,
                                "sell_by_date": str(lot_id.removal_date.date()) if bool(lot_id.removal_date) else None,
                            })

                        CleanDataDict(details_vals)
                        details.append(details_vals)
                    if len(details)<=0:
                        raise UserError('Sem as linhas de quantidade')
                vals = {
                    "uuid": move.uuid or None,
                    "product_name": move.product_id.name if not bool(move.uuid) else None,
                    "line_item_uuid": move.transaction_line_uuid if not bool(move.uuid) else None,
                    "product_uuid": move.product_spt_uuid,
                    "quantity": int(move.quantity_done),
                    "details": details or None,
                }
                CleanDataDict(vals)
                item_lines.append(vals)
            else:
                sdi = '%s' % (str(move.id).zfill(4))
                content_vals = {
                    "type": "product",
                    "sdi": sdi,
                    "lot_based_quantity": int(move.product_uom_qty),
                }
                CleanDataDict(content_vals)
                content.append(content_vals)  
                details_vals = {
                    "quantity": int(move.product_uom_qty),
                    "lot_number": "",
                    "expiration_date": "",
                    "production_date": "",
                    "best_by_date": "",
                    "sell_by_date": "",
                    "manufacturer_address_uuid": "",
                    # "history": [],
                    # "attachments": [],
                    "sdi": sdi,
                    "expiration_date": "",
                }
                CleanDataDict(details_vals)
                
                vals = {
                    "product_name": move.product_id.name,
                    "line_item_uuid": move.transaction_line_uuid,
                    "product_uuid": move.product_spt_uuid,
                    "quantity": int(move.product_uom_qty),
                    "details": [details_vals],
                }
                CleanDataDict(vals)
                item_lines.append(vals)
                
        request_vals = {
            'shipment_type': 'Inbound',
            'shipment_line_items': json.dumps(item_lines),
            'aggregation_data': json.dumps(content),
        }
        return request_vals
    
    def prepare_vals_for_outbound_shipment(self):
        """
        Prepared vals to create outbound shipment in ttrx2
        :return:
        """
        _logger.debug("DEBUG 275: Entrou no prepare_vals_for_outbound_shipment")

        details = []
        item_lines = []
        for move in self.move_ids_without_package:
            x = move
            if move.quantity_done >= 1:
                # for move_line in move.move_line_ids:
                #     qty_in = int(move_line.qty_done or move_line.product_uom_qty)
                #     tracking = move_line.product_id.tracking
                #     if move_line.product_uom_qty >= 1 and bool(move_line.lot_id):
                #         lot_id = move_line.lot_id
                #         lote, serial = self._lot_serial(lot_id.name)
                #         sdi = '%s%s' % (lote,str(move.id).zfill(4))
                #         details_vals = {
                #             "quantity": int(qty_in),
                #             "sdi": sdi,
                #             "lot_number":  lote,                                
                #         }
                #         if hasattr(lot_id, 'life_date'):
                #             details_vals.update({
                #                 "expiration_date": str(lot_id.life_date.date()) if bool(lot_id.life_date) else None,
                #                 "production_date": str(lot_id.production_date.date()) if bool(lot_id.production_date) else None,
                #                 "best_by_date": str(lot_id.use_date.date()) if bool(lot_id.use_date) else None,
                #                 "sell_by_date": str(lot_id.removal_date.date()) if bool(lot_id.removal_date) else None,
                #             })
                #         CleanDataDict(details_vals)
                #         details.append(details_vals)
                vals = {
                    "line_item_uuid": move.transaction_line_uuid,
                    "product_uuid": move.product_spt_uuid,
                    "quantity": int(move.quantity_done),
                    # "details": details,
                }
                item_lines.append(vals)
            else:
                vals = {
                    "line_item_uuid": move.transaction_line_uuid,
                    "product_uuid": move.product_spt_uuid,
                    "quantity": int(move.product_uom_qty),
                    # "details": details,
                }
                item_lines.append(vals)
        # if not bool(item_lines):
        #     raise UserError('There are no products to ship')
        request_vals = {
            'shipment_type': 'Outbound',
            'shipment_line_items': json.dumps(item_lines),
            'is_outbound_shipment_approved': False,
            'invoice_nbr': None,
            'po_nbr': None,
            'release_nbr': None,
            'order_nbr': None,
        }
        return request_vals

    def ShipmentApproveInTTRx(self):
        self.ensure_one()
        res = False
        shipment_type = 'Outbound' if self.picking_type_id.code == 'outgoing' else 'Inbound'
        approve_response = self._PostRecord(self.connector_id, resource='stock.picking.approve', shipment_type=shipment_type, uuid=self.uuid)
        if bool(approve_response) and not bool(approve_response.get('erro')):
            context = dict(self.env.context or {})
            context['no_rewrite'] = True
            self.with_context(context).write({"is_approved": True})
            res = True
        elif self.env.context.get('NotRaiseError',None) in [None,False]:
            raise UserError('Found a error in TTRx, %s' % str(approve_response))
        return res

    def ShipmentPickingInTTRx(self):
        self.ensure_one()
        res = False
        if self.picking_type_id.code == 'outgoing':
            if bool(self.shipment_picking_uuid):
                picking_response = self._GetRecord(self.connector_id, resource='picking.spt', uuid=self.shipment_picking_uuid)
            else:
                shipment_uuid = {'shipment_uuid': self.uuid, 'is_approve_shipment': True}
                picking_response = self._PostRecord(self.connector_id, resource='picking.spt', data=shipment_uuid)
            if bool(picking_response):
                if bool(picking_response.get('erro')) and picking_response['erro'][0].find('TT2LC_pickingS-G00605') > 0:
                    to_self_response = self._GetRecord(self.connector_id, resource='picking.spt.to_self', shipment_uuid=self.uuid)
                    if bool(to_self_response.get('picking_data',False)):
                        picking_response = to_self_response['picking_data']
                if not bool(picking_response.get('erro')):
                    context = dict(self.env.context or {})
                    context['no_rewrite'] = True
                    self.with_context(context).write({"shipment_picking_uuid": picking_response.get('uuid'), "is_approved": True})
                    res = True
            elif self.env.context.get('NotRaiseError',None) in [None,False]:
                raise UserError('Found a error in TTRx, %s' % str(close_response))
        return res

    def ShipmentPickingInTTRxNew(self):
        self.ensure_one()
        res = False
        if self.picking_type_id.code == 'outgoing' and self.is_approved:
            # Verifica se já existe picking 
            pickings = self._get_pickings()
            if len(pickings) == 0:
                picking = self.env['picking.spt'].create({'connector_id': self.connector_id.id, 'shipment_uuid': self.uuid})
                if bool(picking):
                    picking.SyncFromTTRx(picking.connector_id, MySelf=True)
                    res = True
        return res

    def ShipmentPickingCloseInTTRx(self):
        self.ensure_one()
        res = False
        shipment_picking_uuid = self.shipment_picking_ids[0].uuid or self.shipment_picking_uuid
        if self.picking_type_id.code == 'outgoing' and bool(shipment_picking_uuid):
            lines = []
            for move in self.move_lines:
                qtde = 0.0
                for move_line in move.move_line_ids.filtered(lambda x: x.product_uom_qty > 0 and x.qty_done > 0 and x.product_uom_qty >= x.qty_done):
                    qtde += move_line.qty_done
                if qtde == 0:
                    if self.env.context.get('NotRaiseError',None) in [None,False]:
                        raise UserError('Specify a quantity in the operation details')
                    else:
                        return False
                elif qtde > move.product_uom_qty:
                    if self.env.context.get('NotRaiseError',None) in [None,False]:
                        raise UserError('The quantity in the operation details is larger than requested')
                    else:
                        return False
                
            request_vals = self.prepare_vals_for_shipment_picking()
            
            close_response = self._PostRecord(self.connector_id, resource='picking.spt.pick_close', 
                                              shipment_picking_uuid=shipment_picking_uuid,data=request_vals)
            
            if bool(close_response) and not bool(close_response.get('erro')):
                context = dict(self.env.context or {})
                context['no_rewrite'] = True
                if bool(close_response.get('queue_url',False)):
                    queue_indx = str(close_response['queue_url']).rindex('/') + 1
                    if queue_indx > 0 and queue_indx < (len(close_response['queue_url'])-1):
                        queue = close_response['queue_url'][queue_indx:]
                        self.with_context(context).write({'queue_uuid': queue, 'queue_url': close_response['queue_url']})
                        self.env['queue.spt'].SyncFromTTRx(self.connector_id,uuid=queue,ForceUpdate=True)
                else:
                    picking = self.env['picking.spt'].SyncFromTTRx(self.connector_id,MySelf=True)
                res = True
            elif self.env.context.get('NotRaiseError',None) in [None,False]:
                raise UserError('Found a error in TTRx, %s' % str(close_response))
        return res

    def ShipmentOutShippedInTTRx(self):
        self.ensure_one()
        res = False
        shipment_type = 'Outbound' if self.picking_type_id.code == 'outgoing' else 'Inbound'
        shipment_response = self._PostRecord(self.connector_id, resource='stock.picking.shipped', shipment_type=shipment_type, uuid=self.uuid)
        if bool(shipment_response) and not bool(shipment_response.get('erro')):
            context = dict(self.env.context or {})
            context['no_rewrite'] = True
            self.with_context(context).write({"is_shipped": True})
            res = True
        elif self.env.context.get('NotRaiseError',None) in [None,False]:
            raise UserError('Found a error in TTRx, %s' % str(shipment_response))
        return res

    def ShipmentOutPickVerifiedInTTRx(self):
        self.ensure_one()
        res = False
        if self.picking_type_id.code == 'incoming' and not self.is_verified:
            request_vals = self.prepare_vals_shipment_verified()
            verified_response = self._PostRecord(self.connector_id, resource='stock.picking.verified', shipment_type='Inbound', uuid=self.uuid, data=request_vals)
            self.env['tracktrace.log.spt'].addLog(self.connector_id.id, model=self._name, method='POSTSHIPMENTVERIF', message='response is %s' % str(verified_response))
            if bool(verified_response):
                if not bool(verified_response.get('erro')) or str(verified_response.get('erro')).find('Shipment already verified') > 0:
                    context = dict(self.env.context or {})
                    context['no_rewrite'] = True
                    self.with_context(context).write({'is_verified': True})
                    res = True
                elif self.env.context.get('NotRaiseError',None) in [None,False]:
                    raise UserError('Found a error in TTRx, %s' % str(verified_response))
        return res

    def ShipmentOutPickReceivedInTTRx(self):
        self.ensure_one()
        res = False
        if self.picking_type_id.code == 'incoming':
            if not bool(self.storage_spt_id):
                raise UserError('Inform the storage area of the products')
            else:
                shelfs = self.env['shelf.spt'].search_count([('parent_location_id', '=', self.storage_spt_id.stock_location_id.id)])
                if shelfs > 0 and not bool(self.shelf_spt_id):
                    raise UserError('Inform the shelf of the products')
            receive_response = self._PostRecord(self.connector_id, resource='stock.picking.received', shipment_type='Inbound', uuid=self.uuid)
            self.env['tracktrace.log.spt'].addLog(self.connector_id.id, model=self._name, method='POSTSHIPMENTRECEIVE', message='response is %s' % str(receive_response))
            if bool(receive_response) and not bool(receive_response.get('erro')):
                context = dict(self.env.context or {})
                context['no_rewrite'] = True
                self.with_context(context).write({'is_received': True})
                res = True
            elif self.env.context.get('NotRaiseError',None) in [None,False]:
                raise UserError('Found a error in TTRx, %s' % str(receive_response))
        return res

    def _clear_moves_line(self):
        for picking in self:
            if picking.uuid:
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                unlink_ids = set()
                for move in picking.move_lines.filtered(lambda m: m.state not in ('done')):
                    if bool(move.uuid):
                        for move_line in move.move_line_ids.filtered(lambda ml: not bool(ml.uuid)):
                            unlink_ids.add(str(move_line.id))
                    else:
                        for move_line in move.move_line_ids:       
                            unlink_ids.add(str(move_line.id))
                            
                    # if float_is_zero(move_line.qty_done, precision_digits=precision_digits) or \
                    #    float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) or \
                    #    not bool(move_line.move_id) or not bool(move_line.state):
                    #     unlink_ids.add(str(move_line.id))
                if bool(unlink_ids):
                    ids = ','.join(unlink_ids)
                    sql = "DELETE FROM stock_move_line WHERE id in (%s);" % ids
                    self._cr.execute(sql)
                    self._cr.commit()

    def BeforeCreateFromTTRx(self, connector, response, data):
        if bool(self):
            if self.state in ['done','cancel']:
                return False
        return True

    def CreateInTTRx(self, **params):
        self.ensure_one()
        res = False
        if self.picking_type_id.code in ['incoming', 'outgoing']:
            if self.can_send_to_ttr2 and not bool(self.uuid):
                context = dict(self.env.context or {})
                context['no_rewrite'] = True
                resource = "%s.%s" % (self._name,self.picking_type_id.code)
                params['data'] = self.FromOdooToTTRx(connector=self.connector_id)
                if bool(self.BeforeCreateInTTRx(**params)):
                    x=self.connector_id
                    if not params:
                        response = self._PostRecord(self.connector_id,resource,**params)
                        self.env['tracktrace.log.spt'].addLog(self.connector_id.id, model=self._name, method='POSTSHIPMENTRET', message='response is %s' % str(response))
                        if bool(response) and not bool(response.get('erro')):
                            self.with_context(context).write({'uuid': response['uuid'], 'queue_uuid': response.get('queue_uuid',False), 'queue_url': response.get('queue_url',False)})
                            if response.get('queue_uuid',False):
                                x = 0
                                processed = False
                                while x < 10:
                                    sleep(1)
                                    try:
                                        queue = self.env['queue.spt'].SyncFromTTRx(connector=self.connector_id,uuid=response['queue_uuid'])
                                        if bool(queue):
                                            if queue.status == 'DONE':
                                                processed = True
                                                break
                                            elif queue.status == 'FAILED':
                                                self.state = 'cancel'
                                                return False
                                    except Exception as e:
                                        self.connector_id.logger_error('PICKING_QUEUE_ERROR', message=str(e), model=self._name, res_id=self.id)
                                    x += 1
                            else:
                                processed = True
                            if processed:
                                self._CreateUpdateFromTTRx(self.connector_id,primary_model=self.picking_type_id.code,uuid=response['uuid'])
                                if self.connector_id.auto_approve_outbound and self.picking_type_id.code == 'outgoing':
                                    response_approve = self._PostRecord(self.connector_id,'stock.picking.approve',shipment_type='Outbound',uuid=response['uuid'])
                                    if bool(response_approve) and not bool(response_approve.get('erro')):
                                        self.with_context(context).write({'is_approved': True})
                            res = True
                        elif self.env.context.get('NotRaiseError',None) in [None,False]:
                            raise UserError('Erro ao enviar para a TTR (%s)' % response['erro'][0])
                self.AfterCreateInTTRx(**params)
        return res
    
    def prepare_vals_for_shipment_picking(self):
        """
        Prepared values for shipment picking of TTR2
        :return:
        """
        _logger.debug("DEBUG 94: Entrou no prepare_vals_for_shipment_picking")
        self.ensure_one()
        items_list = []
        
        lot_number, quantity = 0, 0
        storage_area_id = self.storage_spt_id
        shelf_spt_id = self.shelf_spt_id
        # local_area_id = self.location_id.location_spt_id
        for move in self.move_lines:
            product_uuid = self.env['product.spt'].search([('product_id','=',move.product_id.id)],limit=1).uuid
            tracking = move.product_id.tracking
            if tracking == 'lot':
                type = 'LOT_BASED'
                if bool(storage_area_id):
                    storage_area_uuid = storage_area_id.uuid
                else:
                    raise UserError('Indicate a storage area registered in the TTRx portal')
                # if self.env['shelf.spt'].search_count([('location_id','=',storage_area_id.stock_location_id.id)]) > 0 and not bool(self.shelf_spt_id):
                #     raise UserError('Indicate a shelf registered in the TTRx portal')
                lot_dict ={}
                for move_line in move.move_line_ids:
                    if move_line.product_uom_qty > 0.0 and move_line.qty_done > 0.0:
                        lot = move_line.lot_id.name
                        if bool(lot_dict.get(lot,False)):
                            lot_dict[lot]['quantity'] += move_line.qty_done
                        else:
                            vals = {
                                "type": type,
                                "product_uuid": product_uuid,
                                "lot_number": lot or None,
                                "quantity": move_line.qty_done,
                                "storage_area_uuid": storage_area_uuid,
                                "storage_area_shelf_uuid": shelf_spt_id.uuid or None,
                            }
                            CleanDataDict(vals)
                            lot_dict[lot] = vals
                for indx, value in lot_dict.items():
                    items_list.append(value)
            else:
                type = 'SIMPLE_SERIAL_BASED'
                lot_dict ={}
                serial = []
                for move_id in line.move_line_ids:
                    if move_line.product_uom_qty > 0.0 and move_line.qty_done == 1.0:
                        lot = move_line.lot_id.name
                        if bool(lot_dict.get(lot,False)):
                            lot_dict[lot]['quantity'] += move_line.qty_done
                            lot_dict[lot]['serial'] += [move_line.lot_id.serial]
                        else:
                            vals = {
                                "type": type,
                                "product_uuid": product_uuid,
                                "lot_number": lot or None,
                                "quantity": move_line.qty_done,
                                "serial": [move_line.lot_id.serial]
                            }
                            CleanDataDict(vals)
                            lot_dict[lot] = vals
                        
                        serial.append(move_id.lot_id.serial)
                        lot_number = move_id.lot_id.ref
                    
                for indx, value in lot_dict.items():
                    items_list.append(value)

        # if self.location_id.is_storage:
        #     location_uuid = self.location_id.storage_uuid
        # else:
        #     location_uuid = self.location_id.uuid
        request_vals = {
            "picking_uuid": self.shipment_picking_ids[0].uuid or self.shipment_picking_uuid,
            "items": json.dumps(items_list),
            "is_complete": 'true',
            "complete_ready_status": 'READY_TO_SHIP',
            "storage_location_uuid": storage_area_id.uuid or None,
            "storage_shelf_uuid": shelf_spt_id.uuid or None,
            "is_remove_from_parent_container": 'true'
        }
        CleanDataDict(request_vals)
        return request_vals
    
    def prepare_vals_for_partial_shipment_picking(self):
        """
        Prepare vals for partially shipment picking
        :return:
        """
        #TODO: Não localizado utilização
        _logger.debug("DEBUG 135: Entrou no prepare_vals_for_partial_shipment_picking")
        
        items_list = []
        lot_number, quantity = 0, 0
        self.ensure_one()
        for line in self.move_ids_without_package:
            serial = []
            for move_id in line.move_line_ids:
                serial.append(move_id.lot_id.name)
                lot_number = move_id.lot_id.ref
            vals = {
                "type": 'SIMPLE_SERIAL_BASED',
                "product_uuid": line.product_id.ttr_uuid,
                "lot_number": lot_number,
                "quantity": line.quantity_done,
                "serials": serial,
            }
            if line.quantity_done:
                items_list.append(vals)
        # if self.location_id.is_storage == True:
        #     location_uuid = self.location_id.storage_uuid
        # else:
        #     location_uuid = self.location_id.uuid
        request_vals = {
            "picking_uuid": self.shipment_picking_uuid,
            "items": json.dumps(items_list),
            "is_complete": 'false',
            # "complete_ready_status": 'SHIPPED',
            # "storage_location_uuid":'1d546d10-f114-47d8-9181-a5347001c0bc',
            "is_remove_from_parent_container": 'true'
            
        }
        return request_vals
    
    def prepare_vals_shipment_verified(self):
        """Prepare vals to Shipment
        
        prepared vals api call for set shipment verified
        :return:
        """
        _logger.debug("DEBUG 318: Entrou no prepare_vals_shipment_verified")
        
        lines = []
        for move in self.move_lines:
            if move.quantity_done >= 1:
                for move_line in move.move_line_nosuggest_ids:
                    lots = []
                    if bool(move_line.uuid):
                        var_line = {
                            'shipping_line_item_uuid': move_line.uuid,
                            'lots': lots,
                        }
                        
        
        request_vals = {
            'shipment_type': 'Inbound',
            'shipment_uuid': self.uuid,
            'storage_area_uuid': self.storage_spt_id.uuid or False,
            'storage_shelf_uuid': self.shelf_spt_id.uuid or None,
            'manual_lot_number_assignation': json.dumps(lines) if len(lines) > 0 else None,
        }
        CleanDataDict(request_vals)
        return request_vals
    
    def prepare_vals_shipment_received(self):
        """
        prepared vals api call for set inbound shipment received
        :return:
        """
        _logger.debug("DEBUG 334: Entrou no prepare_vals_shipment_received")
        request_vals = {
            'shipment_type': 'Inbound',
            'shipment_uuid': self.uuid,
        }
        return request_vals
    
    def get_inbound_shipments(self):
        """
        Schedule Function to get all the inbound shipments from TTRX2
        :return:
        """
        #TODO: Verificar
        _logger.debug("DEBUG 390: Entrou no get_inbound_shipments")
        #                   select * from stock_picking where po_transaction_uuid != '' and shipment_picking_uuid is Null order by id desc;
        # stock_picking_ids = self.search([('state', '=', 'done'), ('is_received', '=', False), ('po_transaction_uuid', '!=', ''), ('uuid', '!=', False)])
        stock_picking_ids = self.search([('po_transaction_uuid', '!=', ''), ('uuid', '=', False), ('state', '!=', 'done')])
        _logger.info("DEBUG 394: search in stock piking = " + repr(stock_picking_ids))
        if stock_picking_ids:
            for shipments in stock_picking_ids:
                _logger.info("DEBUG 397: ID " + str(shipments.id))
                if shipments.po_transaction_uuid and shipments.uuid:
                    request_vals_shipment = {
                        "shipment_type": "Inbound",
                        "shipment_uuid": shipments.uuid,
                        "is_include_line_item_details": True,
                    }
                    get_shipment_response = shipments.company_id.send_request_to_ttr('/shipments/Inbound/' + shipments.uuid, request_vals_shipment, method="GET")
                    delivery_status = get_shipment_response.get('delivery_status')
                    if delivery_status == 'SHIPPED':
                        request_vals = shipments.prepare_vals_shipment_received()
                        set_shipment_received = shipments.company_id.send_request_to_ttr('/shipments/Inbound/' + shipments.uuid + '/set_shipment_received', request_vals, method="POST")
                        request_vals_get = shipments.prepare_vals_shipment_verify()
                        set_shipment_verified = shipments.company_id.send_request_to_ttr('/shipments/Inbound/' + shipments.uuid + '/set_shipment_verified', request_vals_get,
                                                                                         method="POST")
                        if set_shipment_verified.get('uuid') and set_shipment_received.get('uuid'):
                            shipments.update({
                                'is_received': True
                            })
                    continue
                _logger.info("DEBUG 419: ")
                _logger.info(shipments.origin)
                get_shipment_response = shipments.company_id.send_request_to_ttr('/shipments?type=INBOUND&transaction_po_number=' + shipments.origin, method="GET")
                
                if get_shipment_response and get_shipment_response['data']:
                    # TODO do the process to receive
                    _logger.info("DEBUG 425 response: " + repr(str(get_shipment_response['data'])))
                    # TODO UPDATE the table Stock Picking
                    # date_done = now
                    # uuid se tiver
                    # TODO "FOR" Update the table stock_move_line;
                    # lot_name = get_serial_no_ttr2 = Numero serial
                    # lot_ref = Lot #
                    # lot_name LOT#/SERIAL#
                
                _logger.debug("DEBUG 427 response: " + str(get_shipment_response['nb_total_results']))

    def action_create_out(self):
        for picking in self: #self.filtered(lambda pk: pk.uuid == False):
            res = picking.CreateInTTRx()
            if not res:
                raise UserError('This Picking Order cannot be sent to the TTR system')

    def action_approve_out(self):
        for picking in self: #self.filtered(lambda pk: pk.uuid == False):
            res = picking.ShipmentApproveInTTRx()
            if not res:
                raise UserError('This Picking Order cannot be approved in the TTR system')

    def action_picked_out(self):
        for picking in self: #self.filtered(lambda pk: pk.uuid == False):
            if not picking.ShipmentPickingInTTRxNew():
                raise UserError('This Picking Order cannot be picked in the TTR system')

    def action_close_out(self):
        for picking in self: #self.filtered(lambda pk: pk.uuid == False):
            if not picking.ShipmentPickingCloseInTTRx():
                raise UserError('This Picking Order cannot be closed in the TTR system')

    def action_shipped_out(self):
        for picking in self: #self.filtered(lambda pk: pk.uuid == False):
            if not picking.ShipmentOutShippedInTTRx():
                raise UserError('This Picking Order cannot be shipped in the TTR system')

    def action_verified_out(self):
        for picking in self: #self.filtered(lambda pk: pk.uuid == False):
            primary_model = picking.picking_type_id.code
            picking.SyncFromTTRx(picking.connector_id,primary_model=primary_model,MySelf=True)
            if not picking.ShipmentOutPickVerifiedInTTRx():
                raise UserError('This Shipment Order cannot be verified in the TTR system')

    def action_received_out(self):
        for picking in self: #self.filtered(lambda pk: pk.uuid == False):
            if not picking.ShipmentOutPickReceivedInTTRx():
                raise UserError('This Shipment Order cannot be received in the TTR system')

    def action_refresh(self):
        for reg in self:
            primary_model = reg.picking_type_id.code
            reg.SyncFromTTRx(reg.connector_id,primary_model=primary_model,MySelf=True,ForceUpdate=True)
        return True

    def action_assign(self):
        super(stock_picking, self).action_assign()
        for pick in self:
            if pick.picking_type_code == 'incoming' and pick.can_send_to_ttr2:
                res = pick.CreateInTTRx()
                if not res:
                    raise UserError('There was an error when trying to send picking to TTRx, check the Log for more information')

    def action_resend_out(self):
        res = self.WriteInTTRx(self.connector_id, primary_model=self.picking_type_id.code, uuid=self.uuid)

    def button_validate(self):
        for picking in self:
            # try:
                # if picking.uuid:
                #     precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                #     unlink_ids = set()
                #     for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                #         if float_is_zero(move_line.qty_done, precision_digits=precision_digits) or \
                #            float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) or \
                #            not bool(move_line.move_id) or not bool(move_line.state):
                #             unlink_ids.add(str(move_line.id))
                #     if bool(unlink_ids):
                #         ids = ','.join(unlink_ids)
                #         sql = "DELETE FROM stock_move_line WHERE id in (%s);" % ids
                #         self._cr.execute(sql)
                #         self._cr.commit()

            res = True
            transaction_uuid = False
            if self.picking_type_id.code == 'outgoing':
                transaction_uuid = picking.sale_id.uuid
            elif self.picking_type_id.code == 'incoming':
                transaction_uuid = picking.purchase_id.uuid
            if bool(transaction_uuid) and not bool(picking.uuid) and picking.can_send_to_ttr2 and picking.picking_type_code in ['incoming','outgoing']:
                res = picking.CreateInTTRx()
            if picking.uuid:
                if self.picking_type_id.code == 'outgoing':
                    if res and not self.is_approved: 
                        res = self.ShipmentApproveInTTRx()
                    if res and self.is_approved and not self.is_picked and not self.is_picked_closed and not self.is_shipped:
                        res = self.ShipmentPickingInTTRxNew()
                    if res and self.is_approved and self.is_picked and not self.is_picked_closed and not self.is_shipped:
                        res = self.ShipmentPickingCloseInTTRx()
                    if res and self.is_approved and self.is_picked and self.is_picked_closed and not self.is_shipped:
                        res = self.ShipmentOutShippedInTTRx()
                elif self.picking_type_id.code == 'incoming':
                    if res and not self.is_received and not self.is_verified:
                        res = self.ShipmentOutPickReceivedInTTRx()
                    if res and self.is_received and not self.is_verified:
                        res = self.ShipmentOutPickVerifiedInTTRx()
            res_btn = super(stock_picking, picking).button_validate()
            
            if picking.picking_type_id.code == 'incoming' and picking.state == 'done':
                for move_line_id in picking.move_line_ids:
                    lot_id = move_line_id.lot_id.id
                    sql = "UPDATE stock_quant SET reserved_quantity = 0 WHERE lot_id = {:d}".format(lot_id)
                    self._cr.execute(sql)
            
            # except Exception as e:
            #     if bool(self.connector_id):
            #         self.connector_id.logger_error('BUTTON-VALIDATE-TRANSFER', message=str(e),model=self._name,res_id=self.id)
            #     if self.env.context.get('NotRaiseError',None) in [None,False]:
            #         raise UserError(str(e))
            #     else:
            #         return False

        return res_btn

    @api.model
    def create(self, vals):
        res = super().create(vals)
        return res
    
class StockMove(models.Model):
    _inherit = 'stock.move'

    uuid = fields.Char('UUID')     
    product_spt_uuid = fields.Char('Product TTRx UUID',compute='_compute_uuid_ttrx', store=False)
    transaction_line_uuid = fields.Char('Line Item UUID',compute='_compute_uuid_ttrx', store=False)
    product_serials = fields.Char('Product Serials')
    check_shipment = fields.Boolean(related='picking_id.check_shipment')
    sdi = fields.Char("Sdi")

    @api.depends('product_id')
    def _compute_uuid_ttrx(self):
        for move in self:
            move.product_spt_uuid = self.env['product.spt'].search([('product_id','=',move.product_id.id)],limit=1).uuid
            if move.picking_id.picking_type_id.code == 'outgoing':
                move.transaction_line_uuid = move.sale_line_id.uuid
            elif move.picking_id.picking_type_id.code == 'incoming':
                move.transaction_line_uuid = move.purchase_line_id.uuid
            else:
                move.transaction_line_uuid = False
    
    @api.onchange('product_serials')
    def onchange_product_serials(self):
        """
        Onchange function to check if serial is present for a particular product or not
        :return:
        """
        _logger.debug("DEBUG 460: Entrou no onchange_product_serials")
        serial = []
        if self.product_serials:
            for line in self.move_line_ids:
                serial.append(line.get_serial_no_ttr2)
            if self.product_serials in serial:
                for line in self.move_line_ids:
                    if self.product_serials == line.get_serial_no_ttr2:
                        line.lot_name = self.product_serials
                        line.qty_done = 1
            else:
                raise UserError("The serial number is not found for a particular product")

    def _get_new_picking_values(self):
        res = super(StockMove,self)._get_new_picking_values()
        order_id = self.sale_line_id.order_id
        location_id = order_id.shelf_spt_id.stock_location_id or \
                      order_id.storage_spt_id.stock_location_id or \
                      order_id.location_spt_id.stock_location_id
        if bool(self.sale_line_id) and bool(location_id):
            res['location_id'] = location_id.id
        res['shelf_spt_id'] = order_id.shelf_spt_id.id
        res['storage_spt_id'] = order_id.storage_spt_id.id
        res['location_spt_id'] = order_id.location_spt_id.id
        return res

    def CreateUpdateFromTTRx(self, connector, picking, values):
        connector.logger_info('TO/FROM', message='try convert TTRx data to Odoo structure (%s)' % str(values), model=self._name, res_id=self.id)

        product_uuid = values['product']['uuid']
        product_spt_id = self.env['product.spt'].SyncFromTTRx(connector,uuid=product_uuid)
        product_id = product_spt_id.product_id
        sale_line_id = self.env['sale.order.line']
        purchase_line_id = self.env['purchase.order.line']
        group_id = picking.group_id
        
        if not bool(group_id):
            if picking.picking_type_code == 'outgoing':
                group_id = self.env['procurement.group'].create({
                    "partner_id": picking.partner_id.id,
                    "name": picking.name,
                    "move_type": "direct",
                    "sale_id": picking.sale_id.id,
                })

        if picking.picking_type_code == 'outgoing':
            sale_line_id = self.env['sale.order.line'].search([('uuid','=',values['transaction_line_item_uuid'])],limit=1)
        elif picking.picking_type_code == 'incoming':
            purchase_line_id = self.env['purchase.order.line'].search([('uuid','=',values['transaction_line_item_uuid'])],limit=1)
        move = self.env[self._name]
        if values.get('uuid', False):
            move = move.search([('uuid','=',values['uuid'])])
            if not bool(move):
                if picking.picking_type_code == 'outgoing':
                    move = move.search([('sale_line_id','=',sale_line_id.id),('uuid','=',False)],limit=1)
                elif picking.picking_type_code == 'incoming':
                    move = move.search([('purchase_line_id','=',purchase_line_id.id),('uuid','=',False)],limit=1)

        var = {
            'uuid': values.get('uuid', None),
            'date': DateTimeToOdoo(values.get('created_on')) or fields.Datetime.now(),
            'product_id': product_id.id or None,
            'product_uom': product_id.uom_id.id or None,
            'company_id': connector.company_id.id,
            'name': product_id.name,
            'product_uom_qty': values.get('quantity'),
            # 'quantity_done': values.get('quantity'),
            'sale_line_id': sale_line_id.id or None,
            'purchase_line_id': purchase_line_id.id or None,
            'location_dest_id': picking.location_dest_id.id or None,
            'location_id': picking.location_id.id or None,
            'procure_method': 'make_to_stock',
            'warehouse_id': connector.wharehouse_id.id or None,
            'picking_id': picking.id or None,
            'group_id': group_id.id or None,
            'state': 'draft' if not bool(move) else None,
            'picking_type_id': picking.picking_type_id.id or None,
        }
        CleanDataDict(var)
        context = dict(self.env.context or {})
        context['default_picking_id'] = picking.id
        if bool(move):
            move.with_context(context).write(var)
        else:
            move = self.env[self._name].with_context(context).create(var)
        return move

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    uuid = fields.Char('UUID')
    lot_ref = fields.Char('Lot Ref')
    get_serial_no_ttr2 = fields.Char('Serial no')
    
    def CreateUpdateFromTTRx(self, connector, picking, move, details):
        connector.logger_info('TO/FROM', message='try convert TTRx data to Odoo structure (%s)' % str(details), model=self._name, res_id=self.id)

        move_lines = self.env[self._name]
        if picking.picking_type_code == 'outgoing':

            dict_serial = {}
            return_serials = []
            if move.product_id.tracking == 'serial':
                return_serials = self._GetList(connector,resource='stock.picking.serials',
                                          shipment_type='Outbound',
                                          shipment_uuid=picking.uuid,
                                          product_uuid=move.product_id.product_spt_id.uuid)
                if bool(return_serials) and not return_serials[0].get('error',False):
                    for desc_serial in return_serials:
                        serials = desc_serial['serial_no']
                        lot_serial = desc_serial['lot_no']
                        dict_serial[lot_serial] = serials
            serial_pos = 0
            for detail in details:
                for lot in detail['lots']:
                    line_exist = self.env['stock.move.line']
                    if float(detail.get('quantity', 0.0)) >= 1.0:
                        if not bool(dict_serial.get(lot['number'],False)) or len(dict_serial[lot['number']]) <= 0 or serial_pos > len(dict_serial[lot['number']]):
                            # Process Lot
                            lot_id = self.env['stock.production.lot'].search([('name','=',lot['number'])])
                            line_exist = self.env['stock.move.line'].search([('uuid','=',detail['uuid']),('lot_id','=',lot_id.id)],limit=1)
                            
                            picking_lot_item_id = self.env['picking.item.lot.view'].search([('stock_picking_id','=',picking.id),('product_id','=',move.product_id.id),('name','=',lot['number'])],limit=1) \
                                                  if bool(lot_id) else self.env['picking.item.lot.view']
                                                  
                            location_id = self.env['stock.location']
                            if bool(picking_lot_item_id):
                                if bool(picking_lot_item_id.storage_shelf_id):
                                    location_id = picking_lot_item_id.storage_shelf_id.stock_location_id
                                elif bool(picking_lot_item_id.storage_area_id):
                                    location_id = picking_lot_item_id.storage_area_id.stock_location_id
                            if not bool(location_id):
                                location_id = picking.location_id
                            var = {
                                'uuid': detail['uuid'],
                                'company_id': connector.company_id.id,
                                'date': DateTimeToOdoo(detail.get('created_on')) or fields.Datetime.now(),
                                'location_dest_id': picking.location_dest_id.id or None,
                                'location_id': location_id.id or None,
                                'product_uom_id': move.product_id.uom_id.id,
                                # 'product_uom_qty': float(detail.get('quantity') or 0.0),
                                'origin': picking.origin,
                                'product_id': move.product_id.id,
                                'lot_name': lot.get('number', None),
                                'lot_id': lot_id.id or None,
                                'qty_done': float(detail.get('quantity') or 0.0),
                                'move_id': move.id or None,
                                'picking_id': picking.id or None,
                            } 
                        else:
                            # Process Serial
                            serial = dict_serial[lot['number']][serial_pos]
                            lot_id = self.env['stock.production.lot'].search([('name','=',lot['number']),('serial','=',serial)])
                            line_exist = self.env['stock.move.line'].search([('uuid','=',detail['uuid']),('lot_id','=',lot_id.id)],limit=1)
                            picking_lot_item_id = self.env['picking.item.lot.view'].search([('stock_picking_id','=',picking.id),('product_id','=',move.product_id.id),
                                                                                            ('lot_name','=',lot.get('number', None)),('serial_name','=',serial)],
                                                                                            limit=1) if bool(lot_id) else self.env['picking.item.lot.view']
                            location_id = self.env['stock.location']
                            if bool(picking_lot_item_id):
                                if bool(picking_lot_item_id.storage_shelf_id):
                                    location_id = picking_lot_item_id.storage_shelf_id.stock_location_id
                                elif bool(picking_lot_item_id.storage_area_id):
                                    location_id = picking_lot_item_id.storage_area_id.stock_location_id
                            if not bool(location_id):
                                location_id = picking.location_id
                            var = {
                                'uuid': detail['uuid'],
                                'company_id': connector.company_id.id,
                                'date': DateTimeToOdoo(detail.get('created_on')) or fields.Datetime.now(),
                                'location_dest_id': picking.location_dest_id.id or None,
                                'location_id': location_id.id or None,
                                'product_id': move.product_id.id,
                                'product_uom_id': move.product_id.uom_id.id,
                                # 'product_uom_qty': 1.0,
                                'origin': picking.origin,
                                'qty_done': 1.0,
                                'lot_name': lot.get('number', None),
                                'lot_id': lot_id.id or None,
                                'serial_name': dict_serial[lot['number']][serial_pos],
                                'move_id': move.id or None,
                                'picking_id': picking.id or None,
                            } 
                            serial_pos += 1
                        CleanDataDict(var)
                        if bool(line_exist):
                            line_exist.write(var)
                            move_lines |= line_exist
                        else:
                            line_exist = self.create(var)
                            move_lines |= line_exist
        elif picking.picking_type_code == 'incoming':

            # Stock.move.lines
            dict_serial = {}
            return_serials = []
            if move.product_id.tracking == 'serial':
                return_serials = self._GetList(
                                          connector,resource='stock.picking.serials',
                                          shipment_type='Inbound',
                                          shipment_uuid=picking.uuid,
                                          product_uuid=move.product_id.product_spt_id.uuid)
                if len(return_serials) > 0 and not return_serials[0].get('error',False):
                    for desc_serial in return_serials:
                        serials = desc_serial['serial_no']
                        lot_serial = desc_serial['lot_no']
                        dict_serial[lot_serial] = serials
            serial_pos = 0
            for detail in details:
                for lot in detail['lots']:
                    line_exist = self.env['stock.move.line'].search([('uuid','=',detail['uuid'])],limit=1)
                    if float(detail.get('quantity', 0.0)) >= 1.0 or not bool(dict_serial.get(lot['number'],False)) or len(dict_serial[lot['number']]) <= 0 or serial_pos > len(dict_serial[lot['number']]):
                        if not (line_exist):
                            line_exist = self.env['stock.move.line'].search([('uuid','=',False),('picking_id','=',picking.id),('move_id','=',move.id),'|',('lot_name','=',lot['number']),('lot_name','=',False)],limit=1)
                        var = {
                            'uuid': detail['uuid'],
                            'company_id': connector.company_id.id,
                            'date': DateTimeToOdoo(detail.get('created_on')) or fields.Datetime.now(),
                            'location_dest_id': picking.location_dest_id.id or None,
                            'location_id': picking.location_id.id or None,
                            'product_id': move.product_id.id,
                            'product_uom_id': move.product_id.uom_id.id,
                            # 'product_uom_qty': detail.get('quantity', 0.0),
                            'origin': picking.origin,
                            'qty_done': detail.get('quantity', 0.0),
                            'lot_name': lot['number'],
                            'serial_name': False,
                            'move_id': move.id or None,
                            'picking_id': picking.id or None,
                        } 
                    else:
                        if not (line_exist):
                            line_exist = self.env['stock.move.line'].search([('uuid','=',False),('picking_id','=',picking.id),('move_id','=',move.id),
                                                                             '|',('lot_name','=',lot['number']),('lot_name','=',False)],limit=1)
                        var = {
                            'uuid': detail['uuid'],
                            'company_id': connector.company_id.id,
                            'date': DateTimeToOdoo(detail.get('created_on')) or fields.Datetime.now(),
                            'location_dest_id': picking.location_dest_id.id or None,
                            'location_id': picking.location_id.id or None,
                            'product_id': move.product_id.id,
                            'product_uom_id': move.product_id.uom_id.id,
                            # 'product_uom_qty': 1.0,
                            'origin': picking.origin,
                            'qty_done': 1.0,
                            'lot_name': lot['number'],
                            'serial_name': dict_serial[lot['number']][serial_pos],
                            'move_id': move.id or None,
                            'picking_id': picking.id or None,
                        } 
                        serial_pos += 1
                    CleanDataDict(var)
                    if bool(line_exist):
                        line_exist.write(var)
                        move_lines |= line_exist
                    else:
                        line_exist = self.create(var)
                        move_lines |= line_exist
        return move_lines

    # @api.model
    # def create(self, vals):
    #     res = super().create(vals)
    #     if bool(res.move_id.picking_id):
    #         move_id = res.move_id.id
    #         picking_id = res.move_id.picking_id.id
    #         self.env.cr.execute("update stock_move_line SET picking_id = {0:d} WHERE move_id = {0:d};".format(picking_id,move_id))
    #     return res
