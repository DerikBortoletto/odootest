import json
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from ..tools import DateTimeToOdoo, CleanDataDict
import uuid

_logger = logging.getLogger(__name__)

READONLY_STATES = {
    'sale': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}

OUTBOUND_TR = [
    ('SALES', 'Sale'),
    ('TRANSFER', 'Transfer'),
    ('RETURN', 'Return'),
]


class sale_order(models.Model):
    _name = 'sale.order'
    _inherit = ["custom.connector.spt", "sale.order"]
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'uuid': 'uuid'}
    _TTRxToOdoo = {'uuid': 'uuid'}

    def _can_send_to_ttr2(self):
        if not self.no_send_to_ttr2:
            res = super()._can_send_to_ttr2()
            if res:
                itens = self.order_line.filtered(
                    lambda x: bool(x.product_id.product_spt_id.uuid) == True)
                if not bool(self.uuid) and self.state not in ['sale', 'done',
                                                              'cancel']:
                    if len(itens) > 0 and bool(self.location_spt_id):
                        res = True
                else:
                    res = True
        else:
            res = False
        return res

    @api.depends('order_line', 'uuid', 'state', 'location_spt_id',
                 'no_send_to_ttr2')
    def compute_can_send_to_ttr2(self):
        for reg in self:
            reg.can_send_to_ttr2 = reg._can_send_to_ttr2()

    def _auto_data_sync(self):
        connector = self.env['connector.spt'].search(
            [('company_id', '=', self.env.user.company_id.id)], limit=1)
        if bool(connector):
            return not connector.auto_data_sync
        else:
            return True

    uuid = fields.Char("UUID", copy=False)
    location_spt_id = fields.Many2one('locations.management.spt',
                                      string="Location TTRx",
                                      states=READONLY_STATES)
    outbound_tran_sub_type = fields.Selection(OUTBOUND_TR,
                                              string="Transaction Type",
                                              default="SALES",
                                              states=READONLY_STATES)
    storage_spt_id = fields.Many2one('storage.areas.spt', string="Storage TTRx",
                                     states=READONLY_STATES)
    shelf_spt_id = fields.Many2one('shelf.spt', string="Shelf TTRx",
                                   states=READONLY_STATES)
    approved_ttr2 = fields.Boolean('Approved in TTRx', default=False)
    send_to_ttr2 = fields.Boolean('Send to TTRx')
    auto_create_in_ttr2 = fields.Boolean('Auto Send to create to TTRx',
                                         default=False)
    can_send_to_ttr2 = fields.Boolean('Can Send to TTRx',
                                      compute="compute_can_send_to_ttr2",
                                      store=False, readonly=True)
    no_send_to_ttr2 = fields.Boolean('No Send to TTRx', default=lambda
        self: self._auto_data_sync(), copy=False)
    is_editable = fields.Boolean("Editable in TTRx", default=True)
    status_delete_portal = fields.Boolean(copy=False, index=True)

    @api.onchange('location_spt_id')
    def onchange_location_spt_id(self):
        self.storage_spt_id = False
        self.shelf_spt_id = False
        location_id = self.location_spt_id.stock_location_id or self.env[
            'stock.location']
        domain = {'storage_spt_id': [('location_id', '=', location_id.id)],
                  'shelf_spt_id': [('location_id', '=', False)]}
        return {'domain': domain}

    @api.onchange('storage_spt_id')
    def onchange_storage_spt_id(self):
        self.shelf_spt_id = False
        val_id = self.storage_spt_id.stock_location_id.id or False
        domain = {'shelf_spt_id': [('location_id', '=', val_id)]}
        return {'domain': domain}

    def FromOdooToTTRx(self, connector, values={}):
        # myuuid = uuid.uuid4()
        # values.update({
        #     'uuid': str(myuuid)
        #
        # })
        # x = self.action_refresh()
        # y =self._atualizaLinesUUID()
        var = super().FromOdooToTTRx(connector=connector, values=values)

        # TODO: Tratamento quando o partner nao for da TTRx
        if not bool(self.partner_id.uuid):
            partner_uuid = self.partner_id.CreateInTTRx(connector)
            # values.update({
            #     'uuid': str(partner_uuid)
            #
            # })
        else:
            partner_uuid = self.partner_id.uuid

        item_lines = []
        for line in self.order_line:
            if bool(line.product_id.product_spt_id):
                vals = {
                    "product_uuid": line.product_id.product_spt_id.uuid,
                    "quantity": int(line.product_uom_qty),
                    "sort_order": line.id,
                }
                item_lines.append(vals)
            else:
                # TODO: Tratamento de quando o produto nao estiver na TTRx
                raise UserError(
                    "Product " + line.product_id.name + " does not exist in "
                                                        "TTR system.")

        location_uuid = self.location_spt_id.uuid

        invoice_nbr = None
        invoices = self.invoice_ids.filtered(lambda x: x.state == 'posted')
        if len(invoices) > 0:
            invoice_nbr = invoices[0].display_name

        var.update({
            "transaction_type": "sales",
            "location_uuid": location_uuid,
            "trading_partner_uuid": partner_uuid,
            "transaction_date": str(self.date_order.date()),
            "po_nbr": str(self.name),
            "internal_reference_number": str(self.id).zfill(6),
            "release_nbr": "0",
            "is_approved": True,
            "outbound_transaction_sub_type": self.outbound_tran_sub_type or
                                             None,
            # "is_approved_is_ship_transaction": True,
            "line_items": json.dumps(item_lines),
            "sold_by_address_custom_recipient_name": self.company_id.name,
            "sold_by_address_custom_line1": self.company_id.street or None,
            "sold_by_address_custom_line2": self.company_id.street2 or None,
            "sold_by_address_custom_country_code":
                self.company_id.country_id.code or None,
            "sold_by_address_custom_country_name":
                self.company_id.country_id.name or None,
            "sold_by_address_custom_city": self.company_id.city or None,
            "sold_by_address_custom_zip": self.company_id.zip or None,
            "sold_by_address_custom_phone": self.company_id.phone or None,
            "sold_by_address_custom_email": self.company_id.email or None,
            "ship_from_address_custom_recipient_name": self.company_id.name,
            "ship_from_address_custom_line1": self.company_id.street or None,
            "ship_from_address_custom_line2": self.company_id.street2 or None,
            "ship_from_address_custom_country_code":
                self.company_id.country_id.code or None,
            "ship_from_address_custom_country_name":
                self.company_id.country_id.name or None,
            "ship_from_address_custom_city": self.company_id.city or None,
            "ship_from_address_custom_zip": self.company_id.zip or None,
            "ship_from_address_custom_phone": self.company_id.phone or None,
            "ship_from_address_custom_email": self.company_id.email or None,
            "billing_address_custom_recipient_name": self.partner_id.name,
            "billing_address_custom_line1": self.partner_id.street or None,
            "billing_address_custom_line2": self.partner_id.street2 or None,
            "billing_address_custom_country_code":
                self.partner_id.country_id.code or None,
            "billing_address_custom_country_name":
                self.partner_id.country_id.name or None,
            "billing_address_custom_city": self.partner_id.city or None,
            "billing_address_custom_zip": self.partner_id.zip or None,
            "billing_address_custom_phone": self.partner_id.phone or None,
            "billing_address_custom_email": self.partner_id.email or None,
            "ship_to_address_custom_recipient_name": self.partner_id.name,
            "ship_to_address_custom_line1": self.partner_id.street or None,
            "ship_to_address_custom_line2": self.partner_id.street2 or None,
            "ship_to_address_custom_country_code":
                self.partner_id.country_id.code or None,
            "ship_to_address_custom_country_name":
                self.partner_id.country_id.name or None,
            "ship_to_address_custom_city": self.partner_id.city or None,
            "ship_to_address_custom_zip": self.partner_id.zip or None,
            "ship_to_address_custom_phone": self.partner_id.phone or None,
            "ship_to_address_custom_email": self.partner_id.email or None,
            "invoice_nbr": invoice_nbr,
        })
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        var = super().FromTTRxToOdoo(connector=connector, values=values)
        regexist = False
        if values.get('uuid'):
            regexist = self.search_count([('uuid', '=', values['uuid'])]) > 0
        order_lines = self.FromLinesTTRxToOdoo(values['line_items'])
        new_order_lines = []

        if self.search_count([('uuid', '=', values['uuid'])]) > 0:
            for line in order_lines:
                if self.env['sale.order.line'].search_count(
                        [('id', '=', line['id'])]) > 0:
                    nid = line.pop('id')
                    new_order_lines += [(1, nid, line)]
                else:
                    line.pop('id')
                    new_order_lines += [(0, 0, line)]
        else:
            new_order_lines += [(5,)]
            for line in order_lines:
                line.pop('id')
                new_order_lines += [(0, 0, line)]

        partner_id = values.get('trading_partner_uuid') and self.env[
            'res.partner'].SyncFromTTRx(connector,
                                        uuid=values['trading_partner_uuid']) \
                     or \
                     self.env['res.partner']
        payment_term_id = partner_id.property_payment_term_id
        location_spt_id = values.get('location_uuid') and self.env[
            'locations.management.spt'].SyncFromTTRx(connector, uuid=values[
            'location_uuid']) or \
                          self.env['locations.management.spt']

        var.update({
            'uuid': values.get('uuid'),
            'name': _('New') if not regexist else None,
            'origin': 'API TTRx %s' % values.get('order_nbr', ''),
            'create_date': DateTimeToOdoo(
                values.get('created_on', fields.Datetime.now())),
            'date_order': DateTimeToOdoo(
                values.get('transaction_date', fields.Datetime.now())),
            'partner_id': partner_id.id or None,
            'payment_term_id': payment_term_id.id or None,
            'client_order_ref': values.get('custom_id'),
            'send_to_ttr2': False,
            'company_id': connector.company_id.id,
            'currency_id': connector.company_id.currency_id.id,
            'location_spt_id': location_spt_id.id or None,
            'order_line': new_order_lines,
            # 'outbound_transaction_sub_type': values.get(
            # 'outbound_transaction_sub_type','SALES'),
            'approved_ttr2': values.get('is_approved', False),
            'note': values.get('notes'),
            'state': 'draft',
            'is_editable': values.get('is_editable', True),
        })
        CleanDataDict(var)
        return var

    def FromLinesTTRxToOdoo(self, ttr_lines):
        order_line = []
        for ttr_line in ttr_lines:
            product_uuid = ttr_line['product']['uuid']
            product_id = self.env['product.spt'].search(
                [('uuid', '=', product_uuid)], limit=1).product_id
            idx = ttr_line.get('uuid') and \
                  self.env['sale.order.line'].search(
                      [('uuid', '=', ttr_line['uuid'])],
                      limit=1).id or ttr_line.get('sort_order', False)
            var = {
                'uuid': ttr_line.get('uuid'),
                'product_id': product_id.id,
                'product_uom': product_id.uom_id.id,
                'name': product_id.name,
                'product_uom_qty': float(ttr_line.get('quantity')),
                'id': idx,
            }
            CleanDataDict(var)
            order_line.append(var)
        return order_line

    def BeforeCreateFromTTRx(self, connector, response, data):
        if bool(self):
            if self.state in ['sale', 'done', 'cancel']:
                return False
        return True

    def CreateInTTRx(self, connector, **params):
        resource = "%s" % self._name
        params['data'] = self.FromOdooToTTRx(connector=self.connector_id)
        create = False
        if bool(self.BeforeCreateInTTRx(**params)):
            create_response = self._PostRecord(connector, resource, **params)
            if bool(create_response) and not bool(create_response.get('erro')):
                context = dict(self.env.context or {})
                context['no_rewrite'] = True
                self.with_context(context).write(create_response)
                response, data = self.env['sale.order'].GetValuesInTTRx(
                    self.connector_id, uuid=create_response['uuid'])
                order_line = []
                for line in data['order_line']:
                    order_line += [(1, line[1], {'uuid': line[2]['uuid']})]
                self.with_context(context).write({'order_line': order_line})
                create = True

            self.AfterCreateInTTRx(**params)
        return create

    def _atualizaLinesUUID(self):
        context = dict(self.env.context or {})
        context['no_rewrite'] = True
        if bool(self.uuid):
            order = self._GetRecord(self.connector_id, 'sale.order',
                                    uuid=self.uuid)
            if bool(order) and not bool(order.get('erro')):
                idxs = []
                for line_item in order['line_items']:
                    order_line = self.env['sale.order.line'].search(
                        [('uuid', '=', line_item['uuid'])], limit=1)
                    if bool(order_line):
                        idxs.append(order_line.id)
                    else:
                        order_line = self.env['sale.order.line'].search(
                            [('id', '=', line_item['sort_order']),
                             ('order_id', '=', order.id)], limit=1)
                        if not bool(order_line):
                            if len(idxs) == 0:
                                domain = [('uuid', '=', False),
                                          ('product_id', '=', product_id.id),
                                          ('order_id', '=', order_id.id)]
                            else:
                                domain = [('uuid', '=', False),
                                          ('product_id', '=', product_id.id),
                                          ('order_id', '=', order_id.id),
                                          ('id', 'not in', idxs)]
                            order_line = self.env['sale.order.line'].search(
                                domain, limit=1).id
                        if bool(order_line):
                            order_line.with_context(context).write(
                                {'uuid': line_item['uuid']})
                            idxs.append(order_line.id)

    def AfterCreateInTTRx(self, **params):
        self._atualizaLinesUUID()

    def AfterCreateFromTTRx(self, connector, response, data):
        if bool(self.uuid):
            if self.state in ['draft', 'sent']:
                self.action_confirm()
            else:
                self.CreateTTRxPicking()

    def DeleteInTTRx(self, **params):
        self.ensure_one
        res = ""
        if self.uuid:
            res = {'erro': 'Delete is not possible after transaction to TTRX2'}
        return res

    def _action_confirm(self):
        res = True
        shipment_created = False
        # myuuid = uuid.uuid4()
        # self.update({
        #     'uuid': str(myuuid)
        #
        # })
        if bool(self.uuid):
            order_ttrx = self._GetRecord(self.connector_id,
                                         resource='sale.order', uuid=self.uuid)
            shipments = self.env['stock.picking']
            for shipment in order_ttrx.get('shipments', []):
                shipments += self.env['stock.picking'].SyncFromTTRx(
                    self.connector_id, RaiseError=True,
                    primary_model='outgoing', ForceUpdate=True,
                    uuid=shipment['uuid'])
            if len(shipments) > 0:
                for shipment in shipments:
                    if shipment.move_lines:
                        shipment.action_assign()
                    if shipment.is_received:
                        shipment.button_validate()
                shipment_created = True
        if not shipment_created:
            self.order_line._action_launch_stock_rule()
            res = super(sale_order, self)._action_confirm()
        return res

    def action_confirm(self):
        res = super(sale_order, self).action_confirm()
        for order in self:
            if order.can_send_to_ttr2 and not order.no_send_to_ttr2 and not \
                    bool(
                    order.uuid):
                if not bool(order.location_spt_id):
                    raise UserError('Indicate the exit location in TTRx')
                else:
                    ttrx_location = order.location_spt_id
                    if len(ttrx_location) > 0:
                        created = order.CreateInTTRx(order.connector_id)
                        if not created:
                            raise UserError(
                                'The sales order could not be created in '
                                'TTRx. Check the log for more information')
                    else:
                        # TODO: Melhorar, pois existe a possibilidade do
                        #  usuario nao querer enviar a ttrx
                        raise UserError(
                            'This sell order will not be sent to the TTRx '
                            'portal.')
            if bool(order.uuid) and order.connector_id.auto_send_picking == \
                    'auto' and order.partner_id.auto_create_picking == 'auto':
                for pick in order.picking_ids.filtered(
                        lambda x: not bool(x.uuid) and x.state not in ['done',
                                                                       'cancel']):
                    pick.action_assign()
                    pick.CreateInTTRx()

        return res

    def CreateTTRxPicking(self):
        resp, data = self.GetValuesInTTRx(self.connector_id, uuid=self.uuid)
        picking_id = self.env['stock.picking']
        if bool(resp.get('shipments', False)) and len(resp['shipments']) > 0:
            for shipment in resp['shipments']:
                if shipment.get('uuid'):
                    picking_id += self.env['stock.picking'].SyncFromTTRx(
                        self.connector_id, RaiseError=True,
                        primary_model='outgoing', ForceUpdate=True,
                        uuid=shipment['uuid'])
        return picking_id

    def action_cancel(self):
        res = super(sale_order, self).action_cancel()
        for reg in self:
            if reg.uuid and reg.connector_id.auto_delete:
                raise UserError(
                    "Cancellation not possible after transaction to TTRX2")
        return res

    @api.model
    def create(self, values):
        created = super(sale_order, self).create(values)
        if bool(created.uuid) and created.approved_ttr2:
            created.sudo().action_confirm()
        return created

    def _get_orders_to_update_from_ttrx(self):
        """ Gets the rows of the order(s) that have
        not yet been delivered and informs the order to update"""
        line = self.env['sale.order.line']
        orders = set()
        domain = [('state', 'in', ['sale']), ('uuid', '!=', False)]
        if bool(self):
            domain += [('order_id', '=', self.id)]
        lines = line.search(domain)
        for line_item in lines:
            if float_compare(line_item.qty_delivered, line_item.product_uom_qty,
                             precision_digits=0) == (-1):
                orders.add(line_item.order_id.id)
        return orders


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    uuid = fields.Char('UUID from TTR', copy=False, readonly=True)
    status_delete_portal = fields.Boolean(copy=False, index=True)

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields
        genrated by a
        sale order line. procurement group will launch '_run_pull',
        '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or not line.product_id.type in (
            'consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty,
                             precision_digits=precision) >= 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(
                    line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the
                # order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update(
                        {'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update(
                        {'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(
                product_qty, quant_uom)
            locale_id = \
                line.order_id.partner_shipping_id.property_stock_customer
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom, locale_id,
                line.name, line.order_id.name, line.order_id.company_id,
                values))
        if procurements:
            self.env['procurement.group'].run(procurements)
        return True