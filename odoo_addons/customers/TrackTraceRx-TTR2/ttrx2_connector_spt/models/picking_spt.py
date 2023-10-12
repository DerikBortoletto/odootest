import logging

from odoo import models, fields, api, tools
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo, StrToFloat

_logger = logging.getLogger(__name__)

class picking_item_spt(models.Model):
    _name = 'picking.item.spt'
    _description = 'Item Picking'
    _order = 'picking_id,uuid'

    uuid = fields.Char('UUID')
    picking_id = fields.Many2one('picking.spt', string='Picking', required=True, ondelete='cascade', index=True, copy=False)
    picking_type = fields.Char('picking_type')
    shipment_line_item_uuid = fields.Char('Move Line UUID')
    shipment_line_item_id = fields.Many2one('stock.move.line', string='Move Line')
    product_uuid = fields.Char('Product UUID')
    product_spt_id = fields.Many2one('product.spt', string='Product')
    lots = fields.One2many('picking.item.lot.spt', 'picking_id', string='Lots')
    serials = fields.One2many('picking.item.serie.spt', 'picking_id', string='Series')
    quantity = fields.Float('Quantity')
    storage_area_uuid = fields.Char('Storage Area UUID')
    storage_area_id = fields.Many2one('storage.areas.spt',string='Storage Area')
    storage_shelf_uuid = fields.Char('Storage Shelf UUID')
    storage_shelf_id = fields.Many2one('shelf.spt',string='Storage Shelf')

    def CreateUpdateFromTTRx(self, values, picking=False):
        shipment_line_item_id = self.env['stock.move.line'].search([('uuid','=',values['shipment_line_item_uuid']),('move_id','!=',False)]) if values.get('shipment_line_item_uuid', False) else self.env['stock.move.line']
        product_spt_id = self.env['product.spt'].search([('uuid','=',values['product_uuid'])]) if values.get('product_uuid', False) else self.env['product.spt']
        storage_area_id = self.env['storage.areas.spt'].search([('uuid','=',values['storage_area_uuid'])]) if values.get('storage_area_uuid', False) else self.env['storage.areas.spt']
        storage_shelf_id = self.env['shelf.spt'].search([('uuid','=',values['storage_shelf_uuid'])]) if values.get('storage_shelf_uuid', False) else self.env['shelf.spt']

        var_lots = [(5,)]
        for lot in values['lots']:
            var_lot = {'name': lot,}
            var_lots += [(0,0,var_lot)]
        var_serials = [(5,)]
        for serial in values['serials']:
            var_ser = {'name': serial,}
            var_serials += [(0,0,var_ser)]
        var = {
            'picking_id': picking.id if bool(picking) else None,
            'uuid': values['uuid'],
            'picking_type': values.get('picking_type', None),
            'shipment_line_item_uuid': values.get('shipment_line_item_uuid', None),
            'shipment_line_item_id': shipment_line_item_id.id or None,
            'product_uuid': values.get('product_uuid', None),
            'product_spt_id': product_spt_id.id or None,
            'lots': var_lots,
            'serials': var_serials,
            'quantity': float(values.get('quantity', 0)),
            'storage_area_uuid': values.get('storage_area_uuid', None),
            'storage_area_id': storage_area_id.id or None,
            'storage_shelf_uuid': values.get('storage_shelf_uuid', None),
            'storage_shelf_id': storage_shelf_id.id or None,
        }
        CleanDataDict(var)
        return var

class picking_item_lot_spt(models.Model):
    _name = 'picking.item.lot.spt'
    
    picking_id = fields.Many2one('picking.item.spt', string='Picking Item', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Char('Lot Number')
    
class picking_item_serie_spt(models.Model):
    _name = 'picking.item.serie.spt'
    
    picking_id = fields.Many2one('picking.item.spt',string='Picking Item', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Char('Serial Number')

class picking_spt(models.Model):
    _name = 'picking.spt'
    _inherit = "custom.connector.spt"
    _description = 'Shipment Picking'
    _order = 'uuid'
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'uuid': 'uuid'}
    _TTRxToOdoo = {'uuid':'uuid'}
    _rec_name = 'uuid'


    uuid = fields.Char('UUID', copy=False)
    created_on = fields.Datetime('Create On', readonly=True, copy=False)
    shipment_uuid = fields.Char('Outbound Shipment UUID', compute="_get_shipment_uuid", inverse='_set_shipment_uuid', store=True, copy=False)
    stock_picking_id = fields.Many2one('stock.picking', string='Transfer', domain=[('uuid','!=',False)]) 
    trading_partner_uuid = fields.Char('Outbound Shipment UUID', compute="_get_trading_partner_uuid", inverse='_set_trading_partner_uuid', store=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner')

    location_uuid = fields.Char('Location UUID', compute="_get_location_uuid", inverse='_set_location_uuid', store=True, copy=False)
    location_spt_id = fields.Many2one('locations.management.spt', string='Location')

    storage_area_uuid = fields.Char('Storage UUID', compute="_get_storage_uuid", inverse='_set_storage_uuid', store=True, copy=False)
    storage_area_id = fields.Many2one('storage.areas.spt', compute="_get_storage_shelf", string='Storage Area', store=True)

    shelf_uuid = fields.Char('Shelf UUID', compute="_get_shelf_uuid", inverse='_set_shelf_uuid', store=True, copy=False)
    shelf_id = fields.Many2one('shelf.spt', string='Shelf', compute="_get_storage_shelf", store=True)

    participant_uuid = fields.Char('Participant UUID', copy=False)
    participant_name = fields.Char('Participant Name', copy=False)
    is_session_closed = fields.Boolean('Shipped',default=False)
    session_closed = fields.Datetime('Session Closed On', copy=False)

    items = fields.One2many('picking.item.spt','picking_id',string='Items')
    
    products_count_picked = fields.Integer(string='# Products Picked')
    items_count_picked = fields.Integer(string='# Products Picked')
    status = fields.Char('TTRx Status', copy=False)
    active = fields.Boolean(default=True)
    shipment_notes = fields.Text(string='Description')

    @api.depends('items.storage_area_id','items.storage_shelf_id')
    def _get_storage_shelf(self):
        if bool(self.items):
            self.storage_area_id = self.items[0].storage_area_id
            self.shelf_id = self.items[0].storage_shelf_id
        else:
            self.storage_area_id = False
            self.shelf_id = False
        
    @api.depends('stock_picking_id')
    def _get_shipment_uuid(self):
        for pick in self:
            pick.shipment_uuid = self.stock_picking_id.uuid or ''
            
    @api.onchange('shipment_uuid')
    def _set_shipment_uuid(self):
        for pick in self:
            stock_picking = self.env['stock.picking'].search([('uuid','=',pick.shipment_uuid)]) if bool(pick.shipment_uuid) else \
                            self.env['stock.picking']
            pick.stock_picking_id = stock_picking

    @api.depends('partner_id')
    def _get_trading_partner_uuid(self):
        for pick in self:
            pick.trading_partner_uuid = self.partner_id.uuid or ''
            
    @api.onchange('trading_partner_uuid')
    def _set_trading_partner_uuid(self):
        for pick in self:
            partner = self.env['res.partner'].search([('uuid','=',pick.trading_partner_uuid)]) if bool(pick.trading_partner_uuid) else \
                      self.env['res.partner']
            pick.partner_id = partner

    @api.depends('location_spt_id')
    def _get_location_uuid(self):
        for pick in self:
            pick.location_uuid = self.location_spt_id.uuid or ''
            
    @api.onchange('location_uuid')
    def _set_location_uuid(self):
        for pick in self:
            location = self.env['locations.management.spt'].search([('uuid','=',pick.location_uuid)]) if bool(pick.location_uuid) else \
                       self.env['locations.management.spt']
            pick.location_spt_id = location

    @api.depends('storage_area_id')
    def _get_storage_uuid(self):
        for pick in self:
            pick.storage_area_uuid = self.storage_area_id.uuid or ''
            
    @api.onchange('storage_area_uuid')
    def _set_storage_uuid(self):
        for pick in self:
            storage_area = self.env['storage.areas.spt'].search([('uuid','=',pick.storage_area_uuid)]) if bool(pick.storage_area_uuid) else \
                           self.env['storage.areas.spt']
            pick.storage_area_id = storage_area

    @api.depends('shelf_id')
    def _get_shelf_uuid(self):
        for pick in self:
            pick.shelf_uuid = self.shelf_id.uuid or ''
            
    @api.onchange('shelf_uuid')
    def _set_shelf_uuid(self):
        for pick in self:
            shelf = self.env['shelf.spt'].search([('uuid','=',pick.shelf_uuid)]) if bool(pick.shelf_uuid) else \
                    self.env['shelf.spt']
            pick.shelf_id = shelf

    def FromOdooToTTRx(self, connector, values={}):
        var = super(picking_spt,self).FromOdooToTTRx(connector=connector,values=values)

        is_approve_shipment = self.stock_picking_id.is_approved if not bool(self.uuid) else None

        var.update({        
            'uuid': values.get('uuid', self.uuid) or None,
            'shipment_uuid': values.get('shipment_uuid', self.shipment_uuid),
            'trading_partner_uuid': None,
            'location_uuid': None,
            'storage_area_uuid': None,
            'shelf_uuid': None,
            'participant_uuid': None,
            'participant_name': None,
            'is_session_closed': None,
            'session_closed': None,
            'products_count_picked': None,
            'items_count_picked': None,
            'status': None,
            'is_voided':  None,
            'shipment_notes': None,
            'is_approve_shipment': is_approve_shipment,
        })
        CleanDataDict(var)
        return var
 
    def FromTTRxToOdoo(self, connector, values):
        var = super(picking_spt,self).FromOdooToTTRx(connector=connector,values=values)
        items = []
        if values.get('uuid'):
            items = self._GetList(connector, 'stock.picking.receiving.items', uuid=values['uuid'])
        var_items = [(5,)]
        if bool(items) and not items[0].get('error',False):
            for item in items:
                var_item = self.env['picking.item.spt'].CreateUpdateFromTTRx(item)
                var_items += [(0, 0, var_item)]
            
        stock_picking_id = self.env['stock.picking'].search([('uuid','=',values.get('outbound_shipment_uuid'))])
        partner_id = self.env['res.partner'].search([('uuid','=',values.get('trading_partner_uuid'))])
        location_uuid = values.get('location_uuid', None)
        location_spt_id = self.env['locations.management.spt'].search([('uuid','=',values['location_uuid'])]) if bool(location_uuid) else self.env['locations.management.spt']
        storage_area_uuid = None
        storage_area_spt_id = self.env['storage.areas.spt'].search([('uuid','=',storage_area_uuid)]) if bool(storage_area_uuid) else self.env['storage.areas.spt']
        shelf_uuid = None
        shelf_spt_id = self.env['shelf.spt'].search([('uuid','=',shelf_uuid)]) if bool(storage_area_uuid) else self.env['shelf.spt']
        var.update({
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'shipment_uuid': values.get('outbound_shipment_uuid'),
            'stock_picking_id': stock_picking_id.id or None,
            'trading_partner_uuid': values.get('trading_partner_uuid'),
            'partner_id': partner_id.id or None,
            'location_uuid': location_uuid,
            'location_spt_id': location_spt_id.id or None,
            'storage_area_uuid': storage_area_uuid,
            'storage_area_spt_id': storage_area_spt_id.id or None,
            'shelf_uuid': shelf_uuid,
            'shelf_spt_id': shelf_spt_id.id or None,
            'participant_uuid': values.get('participant_uuid'),
            'participant_name': values.get('participant_name'),
            'is_session_closed': values.get('is_session_closed'),
            'session_closed': values.get('session_closed'),
            'products_count_picked': values.get('products_count_picked'),
            'items_count_picked': values.get('items_count_picked'),
            'status': values.get('status'),
            'active': not values.get('is_voided',False),
            'shipment_notes': values.get('shipment_notes'),
            'items': var_items,
        })
        CleanDataDict(var)
        return var

class picking_item_lot_view(models.Model):
    _name = 'picking.item.lot.view'
    _auto = False
    _order = 'id, lot_id'

    uuid = fields.Char('UUID')
    picking_id = fields.Many2one('picking.spt',string='Picking SPT')
    stock_picking_id = fields.Many2one('stock.picking',string='Transfer')
    lot_id = fields.Many2one('picking.item.lot.spt',string='Lot')
    name = fields.Char('Lot Number')
    picking_type = fields.Char('picking_type')
    shipment_line_item_uuid = fields.Char('Move Line UUID')
    shipment_line_item_id = fields.Many2one('stock.move.line', string='Move Line')
    product_uuid = fields.Char('Product UUID')
    product_spt_id = fields.Many2one('product.spt', string='Product Spt')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float('Quantity')
    storage_area_uuid = fields.Char('Storage Area UUID')
    storage_area_id = fields.Many2one('storage.areas.spt',string='Storage Area')
    storage_shelf_uuid = fields.Char('Storage Shelf UUID')
    storage_shelf_id = fields.Many2one('shelf.spt',string='Storage Shelf')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'picking_item_lot_view')
        self.env.cr.execute("""
            CREATE VIEW picking_item_lot_view AS (
                SELECT
                    PIS.id as id,
                    PCK.stock_picking_id as stock_picking_id,
                    PIS.picking_id as picking_id,
                    LOT.id as lot_id,
                    LOT.name as name,
                    PIS.uuid as uuid,
                    PIS.picking_type as picking_type,
                    PIS.shipment_line_item_uuid as shipment_line_item_uuid,
                    PIS.shipment_line_item_id as shipment_line_item_id,
                    PIS.product_uuid as product_uuid,
                    PIS.product_spt_id as product_spt_id,
                    PRO.product_id as product_id,
                    PIS.quantity as quantity,
                    PIS.storage_area_uuid as storage_area_uuid,
                    PIS.storage_area_id as storage_area_id,
                    PIS.storage_shelf_uuid as storage_shelf_uuid,
                    PIS.storage_shelf_id as storage_shelf_id
                FROM picking_item_lot_spt LOT
                    LEFT JOIN picking_item_spt PIS ON (LOT.picking_id = PIS.id)
                    LEFT JOIN picking_spt PCK ON (PIS.picking_id = PCK.id)
                    LEFT JOIN product_spt PRO ON (PIS.product_spt_id = PRO.id)            )
            """)

class picking_item_serial_view(models.Model):
    _name = 'picking.item.serial.view'
    _auto = False
    _order = 'id, lot_id'

    uuid = fields.Char('UUID')
    picking_id = fields.Many2one('picking.spt',string='Picking SPT')
    stock_picking_id = fields.Many2one('stock.picking',string='Transfer')
    serial_id = fields.Many2one('picking.item.serie.spt',string='Serial')
    serial_name = fields.Char('Serial Number')
    lot_id = fields.Many2one('picking.item.lot.spt',string='Lot')
    lot_name = fields.Char('Lot Number')
    name = fields.Char('Lot/serial Number')
    picking_type = fields.Char('picking_type')
    shipment_line_item_uuid = fields.Char('Move Line UUID')
    shipment_line_item_id = fields.Many2one('stock.move.line', string='Move Line')
    product_uuid = fields.Char('Product UUID')
    product_spt_id = fields.Many2one('product.spt', string='Product Spt')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float('Quantity')
    storage_area_uuid = fields.Char('Storage Area UUID')
    storage_area_id = fields.Many2one('storage.areas.spt',string='Storage Area')
    storage_shelf_uuid = fields.Char('Storage Shelf UUID')
    storage_shelf_id = fields.Many2one('shelf.spt',string='Storage Shelf')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'picking_item_serial_view')
        self.env.cr.execute("""
            CREATE VIEW picking_item_serial_view AS (
                SELECT
                    PIS.id as id,
                    PCK.stock_picking_id as stock_picking_id,
                    PIS.picking_id as picking_id,
                    SER.id as serial_id,
                    SER.name as serial_name,
                    LOT.id as lot_id,
                    LOT.name::text || SER.name as name,
                    LOT.name as lot_name,
                    PIS.uuid as uuid,
                    PIS.picking_type as picking_type,
                    PIS.shipment_line_item_uuid as shipment_line_item_uuid,
                    PIS.shipment_line_item_id as shipment_line_item_id,
                    PIS.product_uuid as product_uuid,
                    PIS.product_spt_id as product_spt_id,
                    PRO.product_id as product_id,
                    PIS.quantity as quantity,
                    PIS.storage_area_uuid as storage_area_uuid,
                    PIS.storage_area_id as storage_area_id,
                    PIS.storage_shelf_uuid as storage_shelf_uuid,
                    PIS.storage_shelf_id as storage_shelf_id
                FROM picking_item_serie_spt SER
                    LEFT JOIN picking_item_spt PIS ON (SER.picking_id = PIS.id)
                    LEFT JOIN picking_spt PCK ON (PIS.picking_id = PCK.id)
                    JOIN picking_item_lot_spt LOT ON (PIS.id = LOT.picking_id)
                    LEFT JOIN product_spt PRO ON (PIS.product_spt_id = PRO.id)
            )
            """)


    