import json
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_compare
from ..tools import DateTimeToOdoo, CleanDataDict

_logger = logging.getLogger(__name__)





class stock_picking(models.Model):
    _name = 'stock.picking'
    _inherit = ["custom.connector.spt","stock.picking"]
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'uuid':'uuid'}
    _TTRxToOdoo = {'uuid':'uuid'}

    uuid = fields.Char('UUID in TTR',readonly=True,copy=False)    
    locations_id = fields.Many2one('locations.management.spt', 'Location')
    po_nbr = fields.Char('PO Number')
    internal_reference_number = fields.Char('Internal Reference Nbr')
    release_nbr = fields.Char('Release Number')
    transaction_date = fields.Date('Order Date')
    billing_address = fields.Many2one('trading.partner.address.spt', 'Bought By')
    ship_from_address = fields.Many2one('trading.partner.address.spt', 'Ship From')
    ship_to_address = fields.Many2one('trading.partner.address.spt', 'Ship To')
    sold_by_address = fields.Many2one('trading.partner.address.spt', 'Sold By')
    shipment_picking_uuid = fields.Char('Picking uuid')
    po_transaction_uuid = fields.Char("Transaction UUID")
    check_shipment = fields.Boolean(compute='_compute_shipment_type')
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        readonly=False, required=True,
    )
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id,
        readonly=False, required=True,
    )
    inbound_shipment_id = fields.Char('Inbound Shipment ID')
    outbound_shipment_id = fields.Char('Outbound Shipment ID')
    container_serial = fields.Many2one('container.spt',string='Container Serial')
    is_received = fields.Boolean('Is Received')
    is_closed = fields.Boolean('Is Closed in TTR', default=False)
    send_to_ttr2 = fields.Boolean('Send to TTRx', default=False)

    @api.onchange('location_id')
    def onchange_location_id(self):
        _logger.debug("DEBUG 51: Entrou no onchange_location_id")
        location = self.sale_id.source_location
        vals = []
        for line in location.storage_area_ids:
            vals.append(line.id)
        vals.append(location.id)
        domain = {'location_id': [('id', 'in', vals)]}
        return {'domain': domain}
    
    @api.onchange('location_dest_id')
    def onchange_location_dest_id(self):
        _logger.debug("DEBUG 64: Entrou no onchange_location_dest_id")
        po_obj = self.env['purchase.order'].search([('name', '=', self.origin)])
        location = po_obj.picking_type_id.default_location_dest_id
        vals = []
        for line in location.storage_area_ids:
            if line.is_storage:
                vals.append(line.id)
        vals.append(location.id)
        domain = {'location_dest_id': [('id', 'in', vals)]}
        return {'domain': domain}
    
    @api.depends('picking_type_id')
    def _compute_shipment_type(self):
        _logger.debug("DEBUG 79: Entrou no _compute_shipment_type")
        for rec in self:
            if rec.picking_type_id.code == 'incoming':
                rec.check_shipment = True
            else:
                rec.check_shipment = False
 
    def FromOdooToTTRx(self, values={}):
        var = super().FromOdooToTTRx(values=values)
        if self.picking_type_id.code == 'outgoing':
            request_vals_shipment = self.prepare_vals_for_outbound_shipment()
            var.update(request_vals_shipment)
        elif self.picking_type_id.code == 'incoming':
            request_vals_shipment = self.prepare_vals_for_incoming_shipment()
            var.update(request_vals_shipment)
        CleanDataDict(var)
        return var
    
    def FromTTRxToOdoo(self, values):
        # self.ensure_one()
        var = super().FromTTRxToOdoo(values=values)
        CleanDataDict(var)
        return var

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

        aggregation_data = {
            "type": "container",
            "serial": self.container_serial.name
        }        
        
        item_lines = []
        content = []
        for move in self.move_ids_without_package:
            if move.quantity_done >= 1:
                details = []
                for move_line in move.move_line_ids:
                    if move_line.qty_done == 1 and bool(move_line.lot_id):
                        lot_id = move_line.lot_id
                        lote, serial = self._lot_serial(lot_id.name)
                        content_vals = {"type": "product",
                                        "serial": move_line.lot_name,
                                        "sdi": serial} 
                        content.append(content_vals)                       
                        details_vals = {
                            "quantity": int(move_line.qty_done),
                            "sdi": serial,
                            "lot_number":  lote,                                
                            "expiration_date": str(lot_id.life_date.date()) if bool(lot_id.life_date) else None,
                            "production_date": str(lot_id.production_date.date()) if bool(lot_id.production_date) else None,
                            "best_by_date": str(lot_id.use_date.date()) if bool(lot_id.use_date) else None,
                            "sell_by_date": str(lot_id.removal_date.date()) if bool(lot_id.removal_date) else None,
                        }
                        CleanDataDict(details_vals)
                        details.append(details_vals)
                vals = {
                    "line_item_uuid": move.transaction_line_uuid,
                    "product_uuid": move.product_spt_uuid,
                    "quantity": int(move.quantity_done),
                    "details": details,
                }
                CleanDataDict(vals)
                item_lines.append(vals)
        aggregation_data['content'] = content
        request_vals = {
            'shipment_type': 'Inbound',
            'shipment_line_items': json.dumps(item_lines),
            'aggregation_data': json.dumps([aggregation_data]),
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
            if move.reserved_availability >= 1:
                for move_line in move.move_line_ids:
                    if move_line.product_uom_qty == 1 and bool(move_line.lot_id):
                        lot_id = move_line.lot_id
                        lote, serial = self._lot_serial(lot_id.name)
                        details_vals = {
                            "quantity": int(move_line.product_uom_qty),
                            "sdi": serial,
                            "lot_number":  lote,                                
                            "expiration_date": str(lot_id.life_date.date()) if bool(lot_id.life_date) else None,
                            "production_date": str(lot_id.production_date.date()) if bool(lot_id.production_date) else None,
                            "best_by_date": str(lot_id.use_date.date()) if bool(lot_id.use_date) else None,
                            "sell_by_date": str(lot_id.removal_date.date()) if bool(lot_id.removal_date) else None,
                        }
                        details.append(details_vals)
                vals = {
                    "line_item_uuid": move.transaction_line_uuid,
                    "product_uuid": move.product_spt_uuid,
                    "quantity": int(move.reserved_availability),
                    "details": details,
                }
                item_lines.append(vals)
        request_vals = {
            'shipment_type': 'Outbound',
            'shipment_line_items': json.dumps(item_lines),
        }
        return request_vals
    

    def CreateInTTRx(self, **params):
        if self.picking_type_id.code in ['incoming', 'outgoing']:
            resource = "%s.%s" % (self._name,self.picking_type_id.code)
            params['data'] = self.FromOdooToTTRx()
            if bool(self.BeforeCreateInOdoo(**params)):
                create_response = self._PostRecord(self.connector_id, resource, **params) 
                if bool(create_response) and not bool(create_response.get('erro')):
                    context = dict(self.env.context or {})
                    context['no_rewrite'] = True
                    if self.picking_type_id.code == 'outgoing':
                        self.with_context(context).write({'outbound_shipment_id': create_response['uuid']})
                        shipment_uuid = {'shipment_uuid': self.outbound_shipment_id}
                        picking_response = self._PostRecord(self.connector_id, resource='picking.spt', data=shipment_uuid)
                        if bool(picking_response) and not bool(picking_response.get('erro')):
                            self.with_context(context).shipment_picking_uuid = picking_response.get('uuid')
                            request_vals = self.prepare_vals_for_shipment_picking()
                            close_response = self._PostRecord(self.connector_id, resource='picking.spt.pick_close', 
                                                              shipment_picking_uuid=self.shipment_picking_uuid,data=request_vals)
                            if bool(close_response) and not bool(close_response.get('erro')):
                                self.with_context(context).write({'is_closed': True})
                    elif self.picking_type_id.code == 'incoming':
                        self.with_context(context).write({'inbound_shipment_id': create_response['uuid']})
                        shipment_uuid = {'shipment_uuid': self.inbound_shipment_id}
                        picking_response = self._PostRecord(self.connector_id, resource='picking.spt', data=shipment_uuid)
                        if bool(picking_response) and not bool(picking_response.get('erro')):
                            self.with_context(context).shipment_picking_uuid = picking_response.get('uuid')
                            request_vals = self.prepare_vals_for_shipment_picking()
                            close_response = self._PostRecord(self.connector_id, resource='picking.spt.pick_close', 
                                                              shipment_picking_uuid=self.shipment_picking_uuid,data=request_vals)
                            if bool(close_response) and not bool(close_response.get('erro')):
                                self.with_context(context).write({'is_closed': True})
                else:
                    raise UserError('Erro ao enviar para a TTR (%s)' % create_response['erro'][0])
            self.AfterCreateInOdoo(**params)
        return True
    
    def prepare_vals_for_shipment_picking(self):
        """
        Prepared values for shipment picking of TTR2
        :return:
        """
        _logger.debug("DEBUG 94: Entrou no prepare_vals_for_shipment_picking")
        items_list = []
        lot_number, quantity = 0, 0
        self.ensure_one()
        for line in self.move_ids_without_package:
            serial = []
            product_uuid = self.env['product.spt'].search([('product_id','=',line.product_id.id)],limit=1).uuid
            for move_id in line.move_line_ids:
                serial.append(move_id.lot_id.name)
                lot_number = move_id.lot_id.ref
            vals = {
                "type": 'SIMPLE_SERIAL_BASED',
                "product_uuid": product_uuid,
                "lot_number": lot_number,
                "quantity": line.quantity_done,
                "serials": serial,
            }
            if line.reserved_availability:
                items_list.append(vals)
        # if self.location_id.is_storage:
        #     location_uuid = self.location_id.storage_uuid
        # else:
        #     location_uuid = self.location_id.uuid
        request_vals = {
            "picking_uuid": self.shipment_picking_uuid,
            "items": json.dumps(items_list),
            "is_complete": 'true',
            "complete_ready_status": 'SHIPPED',
            # "storage_location_uuid":'1d546d10-f114-47d8-9181-a5347001c0bc',
            "is_remove_from_parent_container": 'true'
            
        }
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
    
    def button_validate(self):
        res = super(stock_picking, self).button_validate()
        for picking in self:
            if not bool(picking.container_serial) and picking.picking_type_id.code == 'incoming':
                raise UserError('Select container serial')
            picking.CreateInTTRx()
        return res

    def prepare_vals_shipment_verify(self):
        """Prepare vals to Shipment
        
        prepared vals api call for set shipment verified
        :return:
        """
        _logger.debug("DEBUG 318: Entrou no prepare_vals_shipment_verify")
        request_vals = {
            'shipment_type': 'Inbound',
            'shipment_uuid': self.inbound_shipment_id,
            'storage_area_uuid': self.location_dest_id.storage_uuid,
        }
        return request_vals
    
    def prepare_vals_shipment_received(self):
        """
        prepared vals api call for set inbound shipment received
        :return:
        """
        _logger.debug("DEBUG 334: Entrou no prepare_vals_shipment_received")
        request_vals = {
            'shipment_type': 'Inbound',
            'shipment_uuid': self.inbound_shipment_id,
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
        # stock_picking_ids = self.search([('state', '=', 'done'), ('is_received', '=', False), ('po_transaction_uuid', '!=', ''), ('inbound_shipment_id', '!=', False)])
        stock_picking_ids = self.search([('po_transaction_uuid', '!=', ''), ('inbound_shipment_id', '=', False), ('state', '!=', 'done')])
        _logger.info("DEBUG 394: search in stock piking = " + repr(stock_picking_ids))
        if stock_picking_ids:
            for shipments in stock_picking_ids:
                _logger.info("DEBUG 397: ID " + str(shipments.id))
                if shipments.po_transaction_uuid and shipments.inbound_shipment_id:
                    request_vals_shipment = {
                        "shipment_type": "Inbound",
                        "shipment_uuid": shipments.inbound_shipment_id,
                        "is_include_line_item_details": True,
                    }
                    get_shipment_response = shipments.company_id.send_request_to_ttr('/shipments/Inbound/' + shipments.inbound_shipment_id, request_vals_shipment, method="GET")
                    delivery_status = get_shipment_response.get('delivery_status')
                    if delivery_status == 'SHIPPED':
                        request_vals = shipments.prepare_vals_shipment_received()
                        set_shipment_received = shipments.company_id.send_request_to_ttr('/shipments/Inbound/' + shipments.inbound_shipment_id + '/set_shipment_received', request_vals, method="POST")
                        request_vals_get = shipments.prepare_vals_shipment_verify()
                        set_shipment_verified = shipments.company_id.send_request_to_ttr('/shipments/Inbound/' + shipments.inbound_shipment_id + '/set_shipment_verified', request_vals_get,
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
                    # inbound_shipment_id se tiver
                    # TODO "FOR" Update the table stock_move_line;
                    # lot_name = get_serial_no_ttr2 = Numero serial
                    # lot_ref = Lot #
                    # lot_name LOT#/SERIAL#
                
                _logger.debug("DEBUG 427 response: " + str(get_shipment_response['nb_total_results']))

class StockMove(models.Model):
    _inherit = 'stock.move'
    
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
                move.transaction_line_uuid = self.sale_line_id.uuid
            elif move.picking_id.picking_type_id.code == 'incoming':
                move.transaction_line_uuid = self.purchase_line_id.uuid
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





class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    lot_ref = fields.Char('Lot Ref')
    get_serial_no_ttr2 = fields.Char('Serial no')
    
    
    
    def _action_done(self):
        """
        override the default function to create the internal reference also in stock production lot object
        This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and un-reserve if needed in the source
        location.

        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move that's what the override of `write` here
        is done.
        """
        _logger.debug("DEBUG 474: Entrou no _action_done")
        Quant = self.env['stock.quant']
        
        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_to_delete = self.env['stock.move.line']
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                  rounding precision of your unit of measure.' % (ml.product_id.display_name, ml.product_uom_id.name))
            
            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name and not ml.lot_id:
                                lot = self.env['stock.production.lot'].create(
                                    {'name': ml.lot_name, 'product_id': ml.product_id.id, 'ref': ml.lot_ref, 'company_id': self.company_id.id}
                                )
                                ml.write({'lot_id': lot.id})
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.inventory_id:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue
                    
                    if not ml.lot_id:
                        raise UserError('You need to supply a Lot/Serial number for product %s.' % ml.product_id.display_name)
            elif qty_done_float_compared < 0:
                raise UserError('No negative quantities allowed')
            else:
                ml_to_delete |= ml
        ml_to_delete.unlink()
        
        # Now, we can actually move the quant.
        done_ml = self.env['stock.move.line']
        for ml in self - ml_to_delete:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding
                
                # if this move line is force assigned, un-reserve elsewhere if needed
                if not ml.location_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_qty, precision_rounding=rounding) > 0:
                    extra_qty = ml.qty_done - ml.product_qty
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
                # un-reserve what's been reserved
                if not ml.location_id.should_bypass_reservation() and ml.product_id.type == 'product' and ml.product_qty:
                    try:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    except UserError:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                
                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            done_ml |= ml
        # Reset the reserved quantity as we just moved it to the destination location.
        (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
            'product_uom_qty': 0.00,
            'date': fields.Datetime.now(),
        })
