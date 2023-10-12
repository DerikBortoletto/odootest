import json
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from ..tools import DateTimeToOdoo, CleanDataDict
from ..connector.service import get_last_param, get_list_param
from odoo.tools.float_utils import float_compare
import uuid
_logger = logging.getLogger(__name__)

READONLY_STATES = {
    'purchase': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class purchase_order(models.Model):
    _name = 'purchase.order'
    _inherit = ["custom.connector.spt", "purchase.order"]
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'uuid': 'uuid'}
    _TTRxToOdoo = {'uuid': 'uuid'}



    def _can_send_to_ttr2(self):
        if not self.no_send_to_ttr2:
            res = super()._can_send_to_ttr2()
            if res:
                itens = self.order_line.filtered(lambda x: bool(x.product_id.product_spt_id.uuid) == True)
                if not bool(self.uuid) and self.state not in ['purchase', 'done', 'cancel']:
                    if len(itens) > 0 and bool(self.storage_spt_id):
                        res = True
                else:
                    res = True
        else:
            res = False
        return res

    @api.depends('order_line', 'uuid', 'state', 'location_spt_id', 'no_send_to_ttr2')
    def compute_can_send_to_ttr2(self):
        for reg in self:
            reg.can_send_to_ttr2 = reg._can_send_to_ttr2()

    uuid = fields.Char("UUID", copy=False)
    status_delete_portal = fields.Boolean(copy=False, index=True)
    location_spt_id = fields.Many2one('locations.management.spt', states=READONLY_STATES, string="Location TTRx")
    location_id = fields.Many2one('stock.location', string="Location", compute="_get_locations", store=False)
    storage_spt_id = fields.Many2one('storage.areas.spt', string="Storage TTRx", states=READONLY_STATES,
                                     domain="[('stock_location_id','=',location_id)]")
    storage_id = fields.Many2one('stock.location', string="Location", compute="_get_locations", store=False)
    shelf_spt_id = fields.Many2one('shelf.spt', string="Shelf TTRx", states=READONLY_STATES,
                                   domain="[('stock_location_id','=',storage_id)]")
    # send_to_ttr2 = fields.Boolean('Send to TTRx', default=False)
    can_send_to_ttr2 = fields.Boolean('Can Send to TTRx', compute="compute_can_send_to_ttr2", store=False,
                                      readonly=True)
    # can_send_ttr2 = fields.Boolean('Auto Send to TTRx', compute="_auto_send_ttrx", store=False, readonly=True)
    is_editable = fields.Boolean("Editable in TTRx", default=True)
    no_send_to_ttr2 = fields.Boolean('No Send to TTRx', default=False)
    auto_create_in_ttr2 = fields.Boolean('Auto Send to create to TTRx', default=False)

    @api.depends('location_spt_id', 'storage_spt_id')
    def _get_locations(self):
        self.location_id = self.location_spt_id.stock_location_id
        self.storage_id = self.storage_spt_id.stock_location_id

    @api.onchange('location_spt_id')
    def onchange_location_spt_id(self):
        self.storage_spt_id = False
        self.shelf_spt_id = False
        location_id = self.location_spt_id.stock_location_id or self.env['stock.location']
        domain = {'storage_spt_id': [('location_id', '=', location_id.id)],
                  'shelf_spt_id': [('location_id', '=', False)]}
        return {'domain': domain}

    @api.onchange('storage_spt_id')
    def onchange_storage_spt_id(self):
        self.shelf_spt_id = False
        val_id = self.storage_spt_id.stock_location_id.id or False
        domain = {'shelf_spt_id': [('location_id', '=', val_id)]}
        return {'domain': domain}

    @api.onchange('picking_type_id')
    def on_change_picking_type_id(self):
        location_spt = self.env['locations.management.spt']
        if bool(self.picking_type_id):
            location = self.picking_type_id.default_location_dest_id
            location_spt = location_spt.search([('stock_location_id', '=', location.id)], limit=1)
        self.location_spt_id = location_spt

    def from_odoo_to_ttrx(self):
        # var = super().FromOdooToTTRx(connector=connector, values=values)
        try:
            location_spt = \
            self.env['locations.management.spt'].search([('display_name', '=', self.location_spt_id.name)])[
                0].uuid
        except:
            location_spt = self.env['locations.management.spt'].search([('display_name', '=', self.location_spt_id.name)],
                                                                   limit=1).uuid

        location_uuid = location_spt
        var = {}
        # TODO: Tratamento quando o partner nao for da TTRx

        item_lines = []

        if self:
            if self.order_line:
                for line in self.order_line:
                    if bool(line.product_id.product_spt_id):
                        vals = {
                            "product_uuid": line.product_id.product_spt_id.uuid,
                            "quantity": int(line.product_qty),
                            "sort_order": line.id,
                            # "catalog_price": line.price_unit,
                        }
                        item_lines.append(vals)
                    else:
                        # TODO: Tratamento de quando o produto nao estiver na TTRx
                        raise UserError("Product " + line.product_id.name + " does not exist in TTR system.")
            else:
                raise UserError(f'Is not possible to send purchase without products: {self.name}')
        # if not bool(self.location_spt_id) and not bool(
        #         self.picking_type_id.default_location_dest_id.location_spt_id.uuid):
        #     pass
        #     # TODO: Tratamento de quando o default location não estiver na TTRx
        # #             raise UserError("""
        # # Location "%s" does not exist in TTR system.
        # # Set a TrackTrace location in the inventory menu, settings, operation types.
        # # """ % self.picking_type_id.default_location_dest_id.name)
        # elif bool(self.location_spt_id):
        #     location_uuid = self.location_spt_id.uuid
        # else:
        #     location_uuid = self.picking_type_id.default_location_dest_id.location_spt_id.uuid

            invoice_nbr = None
            invoices = self.invoice_ids.filtered(lambda x: x.state == 'posted')
            if len(invoices) > 0:
                invoice_nbr = invoices[0].display_name

            var.update({
                "transaction_type": "purchase",
                "location_uuid": location_uuid,
                "trading_partner_uuid": self.partner_id.uuid,
                "transaction_date": str(self.date_order.date()),
                "line_items": json.dumps(item_lines),
                "sold_by_address_custom_recipient_name": self.partner_id.name,
                "sold_by_address_custom_line1": self.partner_id.street or None,
                "sold_by_address_custom_line2": self.partner_id.street2 or None,
                "sold_by_address_custom_country_code": self.partner_id.country_id.code or None,
                "sold_by_address_custom_country_name": self.partner_id.country_id.name or None,
                "sold_by_address_custom_state_code": "",
                "sold_by_address_custom_city": self.partner_id.city or None,
                "sold_by_address_custom_zip": self.partner_id.zip or None,
                "sold_by_address_custom_phone": self.partner_id.phone or None,
                "sold_by_address_custom_email": self.partner_id.email or None,
                "ship_from_address_custom_recipient_name": self.partner_id.name,
                "ship_from_address_custom_line1": self.partner_id.street or None,
                "ship_from_address_custom_line2": self.partner_id.street2 or None,
                "ship_from_address_custom_country_code": self.partner_id.country_id.code or None,
                "ship_from_address_custom_country_name": self.partner_id.country_id.name or None,
                "ship_from_address_custom_state_code": "",
                "ship_from_address_custom_city": self.partner_id.city or None,
                "ship_from_address_custom_zip": self.partner_id.zip or None,
                "ship_from_address_custom_phone": self.partner_id.phone or None,
                "ship_from_address_custom_email": self.partner_id.email or None,
                "billing_address_custom_recipient_name": self.company_id.name,
                "billing_address_custom_line1": self.company_id.street or None,
                "billing_address_custom_line2": self.company_id.street2 or None,
                "billing_address_custom_country_code": self.company_id.country_id.code or None,
                "billing_address_custom_country_name": self.company_id.country_id.name or None,
                "billing_address_custom_state_code": "",
                "billing_address_custom_city": self.company_id.city or None,
                "billing_address_custom_zip": self.company_id.zip or None,
                "billing_address_custom_phone": self.company_id.phone or None,
                "billing_address_custom_email": self.company_id.email or None,
                "ship_to_address_custom_recipient_name": self.company_id.name,
                "ship_to_address_custom_line1": self.company_id.street or None,
                "ship_to_address_custom_line2": self.company_id.street2 or None,
                "ship_to_address_custom_country_code": self.company_id.country_id.code or None,
                "ship_to_address_custom_country_name": self.company_id.country_id.name or None,
                "ship_to_address_custom_state_code": "",
                "ship_to_address_custom_city": self.company_id.city or None,
                "ship_to_address_custom_zip": self.company_id.zip or None,
                "ship_to_address_custom_phone": self.company_id.phone or None,
                "ship_to_address_custom_email": self.company_id.email or None,
                "invoice_nbr": invoice_nbr,
                "po_nbr": self.name,
                "is_approved": False,
            })
            CleanDataDict(var)
            return var

    def SyncFromTTRx(self, connector, **params):
        for i in self.env['purchase.order'].search([]):
            method = 'GET'
            url = f"/transactions/purchase/{i.uuid}"
            get_response = self.company_id.send_request_to_ttr(
                request_url=url,
                method=method
            )
            if not get_response:
                i.update({'status_delete_portal': True})
        context = dict(self.env.context or {})
        connector.logger_info('TRYSYNCFROMTTRX', message='try sync data from TTRx list in Odoo %s' % str(params),
                              model=self._name, res_id=self.id)
        res = self.env[self._name]
        context['NewOnly'] = bool(params.get('NewOnly', False))
        context['MySelf'] = bool(params.get('MySelf', False))
        context['NoUpdate'] = bool(params.get('NoUpdate', False))
        context['NoCreate'] = bool(params.get('NoCreate', False))
        context['ForceUpdate'] = bool(params.get('ForceUpdate', False))
        context['RaiseError'] = bool(params.get('RaiseError', False))
        if not bool(connector.wharehouse_id):
            erro = """
    The wharehouse was not indicated!
        First configure the following options in the inventory settings:

        * Warehouse Section
        1) Enable "Storage Locations";
        2) Enable "Mult-Step Routes"."""
            connector.logger_error('TRYSYNCFROMTTRX', message=erro, model=self._name, res_id=self.id)
        else:
            primary_model = params.get('primary_model') if bool(params.get('primary_model')) else self.primary_model \
                if hasattr(self, 'primary_model') else None
            resource = "%s.%s" % (self._name, primary_model) if bool(primary_model) else self._name
            if context['MySelf']:
                if not bool(self.ids):
                    return res
                if bool(primary_model):
                    params['primary_model'] = primary_model
                params.update(self.with_context(context)._GetUriParams(resource, primary_model=primary_model))
                res += self.with_context(context)._CreateUpdateFromTTRx(connector, **params)
            else:
                last_param = get_last_param(resource)
                if bool(last_param) and last_param in params:
                    register = self.with_context(context).TTRxSearch(connector, **params)
                    if not bool(register) or context['ForceUpdate']:
                        res += register.with_context(context)._CreateUpdateFromTTRx(connector, **params)
                    else:
                        res += register
                else:
                    data_list = self.with_context(context)._GetList(connector, resource, **params) or []
                    for data in data_list:
                        params_data = {}
                        params_data.update(params)
                        for key in params_data.keys():
                            if not bool(params_data.get(key, False)):
                                params_data[key] = data.get(key, params_data[key])
                        params_data.update(data)
                        param_uri = self.with_context(context)._GetParamsTTRxToURI(resource, params_data)
                        params_data.update(param_uri)
                        update = True
                        if context['NewOnly']:
                            domain = self._GetTTRxDomainToSearch(data)
                            exist = self.search(domain, limit=1)
                            if bool(exist):
                                update = False
                        if update:
                            CleanDataDict(params_data)
                            res += self.with_context(context)._CreateUpdateFromTTRx(connector, **params_data)
        return res

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
        try:
            if bool(response) and not bool(response.get('error')):
                domain = self._GetTTRxDomainToSearch(data)
                exist = self.search(domain, limit=1)
                res = exist.BeforeCreateFromTTRx(connector, response, data)
                if bool(res):
                    if bool(exist):
                        if not NoUpdate:
                            context = dict(self.env.context or {})
                            context['no_rewrite'] = True
                            exist.with_context(context).write(data)
                    else:
                        if not NoCreate:
                            exist = super(purchase_order, self).create(data)
                exist.AfterCreateFromTTRx(connector,response,data)
                exist._cr.commit()
            elif bool(response) and bool(response.get('error',False)):
                connector.logger_error('CREATEUPDATE', message=str(response.get('error','')), model=self._name, res_id=self.id)
                if not self.env.context.get('NotRaiseError',False):
                    raise UserError(response['error'])
        except Exception as e:
            _logger.warning(f"Error creating or updating from portal {e} 1")
            self.env.cr.rollback()
            connector.logger_error('TRYSYNCFROMTTRX', message=str(e), model=self._name, res_id=self.id)
            if self._get_parameter_raise_exception():
                raise UserError(str(e))
            _logger.warning(f"Error creating or updating from portal {e} 2")
        if not exist:
            # raise UserError(response['error'])
            _logger.warning(f"Error creating or updating from portal {response} 3")
        return exist

    def FromTTRxToOdoo(self, connector, values):
        var = super().FromTTRxToOdoo(connector=connector, values=values)
        regexist = False
        if values.get('uuid'):
            order_id = self.search([('uuid', '=', values['uuid'])], limit=1)
            regexist = len(order_id.ids) > 0
        order_lines = self.FromLinesTTRxToOdoo(order_id, values['line_items'])
        new_order_lines = []
        if regexist:
            for line in order_lines:
                if self.env['purchase.order.line'].search_count([('id', '=', line['id'])]) > 0:
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

        partner_id = values.get('trading_partner_uuid') and self.env['res.partner'].SyncFromTTRx(connector, uuid=values[
            'trading_partner_uuid']) or \
                     self.env['res.partner']
        payment_term_id = partner_id.property_supplier_payment_term_id
        location_spt_id = values.get('location_uuid') and self.env['locations.management.spt'].SyncFromTTRx(connector,
                                                                                                            uuid=values[
                                                                                                                'location_uuid']) or \
                          self.env['locations.management.spt']
        picking_type_id = location_spt_id and self.env['stock.picking.type'].search(
            [('default_location_dest_id', '=', location_spt_id.stock_location_id.id)]) or \
                          self.env['stock.picking.type']

        # TODO: Billing Address
        # TODO: Shipping Address

        var.update({
            'uuid': values.get('uuid'),
            'name': values.get('po_nbr', 'New from ttrx'),
            'origin': 'API TTRx %s' % values.get('po_nbr', '') if not regexist else None,
            'create_date': DateTimeToOdoo(values.get('created_on', fields.Datetime.now())),
            'date_order': DateTimeToOdoo(values.get('transaction_date', fields.Datetime.now())),
            'partner_id': partner_id.id or None,
            'payment_term_id': payment_term_id.id or None if not regexist else None,
            'partner_ref': values.get('custom_id'),
            'can_send_to_ttr2': False,
            'company_id': connector.company_id.id,
            'currency_id': connector.company_id.currency_id.id,
            'order_line': new_order_lines,
            'location_spt_id': location_spt_id.id or None,
            'picking_type_id': picking_type_id.id or None,
            'notes': values.get('notes'),
            'state': 'draft' if not regexist else None,
            'is_editable': values.get('is_editable', True),
        })
        CleanDataDict(var)
        return var

    def FromLinesTTRxToOdoo(self, order_id, ttr_lines):
        order_line = []
        idxs = []
        for ttr_line in ttr_lines:
            product_uuid = ttr_line['product']['uuid']
            product_id = self.env['product.spt'].search([('uuid', '=', product_uuid)], limit=1).product_id
            idx = False
            can_change = order_id.state not in ['purchase', 'done', 'cancel'] if bool(order_id) else True
            if bool(order_id):
                if bool(ttr_line.get('uuid')):
                    idx = self.env['purchase.order.line'].search([('uuid', '=', ttr_line['uuid'])], limit=1).id
                if not bool(idx):
                    if len(idxs) == 0:
                        domain = [('uuid', '=', False), ('product_id', '=', product_id.id),
                                  ('order_id', '=', order_id.id)]
                    else:
                        domain = [('uuid', '=', False), ('product_id', '=', product_id.id),
                                  ('order_id', '=', order_id.id), ('id', 'not in', idxs)]
                    idx = self.env['purchase.order.line'].search(domain, limit=1).id
            var = {
                'uuid': ttr_line.get('uuid'),
                'product_id': product_id.id if can_change else None,
                'product_uom': product_id.uom_id.id if can_change else None,
                'name': product_id.name if can_change else None,
                'product_uom_qty': float(ttr_line.get('quantity')) if can_change else None,
                'product_qty': float(ttr_line.get('quantity')) if can_change else None,
                'id': idx if bool(idx) else int(ttr_line['sort_order']) if bool(ttr_line.get('sort_order')) else None,
            }
            CleanDataDict(var)
            order_line.append(var)
        return order_line

    def CreateInTTRx(self, **params):
        resource = "%s" % self._name
        context = dict(self.env.context or {})
        context['no_rewrite'] = True
        create = False
        create_response = self._GetList(connector=self.connector_id, resource=resource, po_nbr=self.name)
        if bool(create_response):
            uuid = create_response[0].get('uuid', False)
            self.with_context(context).write({'uuid': uuid})
            create = True
        else:
            params['data'] = self.FromOdooToTTRx(connector=self.connector_id)
            if bool(self.BeforeCreateInTTRx(**params)):
                create_response = self._PostRecord(self.connector_id, resource, **params)
                if bool(create_response) and not bool(create_response.get('erro')):
                    self.with_context(context).write(create_response)
                    response, data = self.env['purchase.order'].GetValuesInTTRx(self.connector_id,
                                                                                uuid=create_response['uuid'])
                    order_line = []
                    for line in data['order_line']:
                        order_line += [(1, line[1], {'uuid': line[2]['uuid']})]
                    self.with_context(context).write({'order_line': order_line})
                    create = True
                elif bool(create_response) and bool(create_response.get('erro')):
                    erro = "\n".join(create_response['erro'])
                    self.env['tracktrace.log.spt'].addLog(self.connector_id.id, model=self._name, method='TRYCREATE',
                                                          message='try create a new P.O. registry from Odoo to TTRx:\n%s' % erro,
                                                          typein='error')
                self.AfterCreateInTTRx(**params)
        return create

    def _atualizaLinesUUID(self):
        context = dict(self.env.context or {})
        context['no_rewrite'] = True
        if bool(self.uuid):
            order = self._GetRecord(self.connector_id, 'purchase.order', uuid=self.uuid)
            if bool(order) and not bool(order.get('erro')):
                idxs = []
                for line_item in order['line_items']:
                    order_line = self.env['purchase.order.line'].search([('uuid', '=', line_item['uuid'])], limit=1)
                    if bool(order_line):
                        idxs.append(order_line.id)
                    else:
                        order_line = self.env['purchase.order.line'].search(
                            [('id', '=', line_item['sort_order']), ('order_id', '=', order.id)], limit=1)
                        if not bool(order_line):
                            if len(idxs) == 0:
                                domain = [('uuid', '=', False), ('product_id', '=', product_id.id),
                                          ('order_id', '=', order_id.id)]
                            else:
                                domain = [('uuid', '=', False), ('product_id', '=', product_id.id),
                                          ('order_id', '=', order_id.id), ('id', 'not in', idxs)]
                            order_line = self.env['purchase.order.line'].search(domain, limit=1).id
                        if bool(order_line):
                            order_line.with_context(context).write({'uuid': line_item['uuid']})
                            idxs.append(order_line.id)

    def AfterCreateInTTRx(self, **params):
        if bool(self.uuid):
            self._atualizaLinesUUID()
            if self.connector_id.auto_send_picking == 'auto' and self.partner_id.auto_create_picking == 'auto':
                pickings = self.picking_ids.filtered(lambda x: not bool(x.uuid) and x.state not in ('done', 'cancel'))
                for picking in pickings:
                    picking.CreateInTTRx()

    def AfterCreateFromTTRx(self, connector, response, data):
        if bool(self):
            if bool(self.uuid):
                self._atualizaLinesUUID()
                if self.state in ['draft', 'sent', 'to_approve']:
                    self.button_confirm()
                else:
                    self.CreateTTRxPicking()

    def CreateTTRxPicking(self):
        resp, data = self.GetValuesInTTRx(self.connector_id, uuid=self.uuid)
        picking_id = self.env['stock.picking']
        if bool(resp.get('shipments', False)) and len(resp['shipments']) > 0:
            for shipment in resp['shipments']:
                if shipment.get('uuid'):
                    picking_id += self.env['stock.picking'].SyncFromTTRx(self.connector_id, RaiseError=True,
                                                                         primary_model='incoming', ForceUpdate=True,
                                                                         uuid=shipment['uuid'])
        return picking_id

    def DeleteInTTRx(self, **params):
        self.ensure_one
        res = {}
        if self.uuid:
            method = 'GET'
            url = f"/transactions/purchase/{self.uuid}"
            get_response = self.company_id.send_request_to_ttr(
                request_url=url,
                method=method
            )
            if get_response:
                get_purchase_status = get_response.get('is_approved', '')
                if get_purchase_status:
                    res = {'erro': 'Delete is not possible after transaction to TTRX2'}
            else:
                return
        return res

    @api.model
    def create(self, values):
        res = super(purchase_order, self).create(values)
        myuuid = uuid.uuid4()
        for order in self:
            order.update({
                'uuid': "9b974b88-6bd0-49b8-bbcf-f4a9079a8b2e"

            })
        return res

    def button_confirm(self):
        """ Confirm Button

        On confirming the PO in odoo Transaction has been created in TTR2
        :return:
        """
        for order in self:
            order.update({
                'uuid': ""

            })
        self.action_refresh()
        for order in self:
            if not bool(order.uuid) or order.uuid == "9b974b88-6bd0-49b8-bbcf-f4a9079a8b2e":
                if order.can_send_to_ttr2 and not order.no_send_to_ttr2:
                    created = order.CreateInTTRx()
                    if not created:
                        raise UserError('A Purchase Order cannot be sent to the TTR system')
            elif bool(self.uuid) and self.connector_id.auto_send_picking == 'auto':
                pickings = self.picking_ids.filtered(lambda x: not bool(x.uuid) and x.state not in ('done', 'cancel'))
                for picking in pickings:
                    picking.CreateInTTRx()
        res = super(purchase_order, self).button_confirm()
        return res

    def _create_picking(self):
        StockPicking = picking = self.env['stock.picking']
        MoveToSend = self.env['stock.move']
        MoveToAssign = self.env['stock.move']

        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                if bool(order.uuid):
                    pickings = order.CreateTTRxPicking()
                    if len(pickings) > 0:
                        picking = pickings[0]
                if not bool(picking):
                    order = order.with_company(order.company_id)
                    pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                    if not pickings:
                        res = order._prepare_picking()
                        res['location_spt_id'] = order.location_spt_id.id
                        res['storage_spt_id'] = order.storage_spt_id.id
                        res['shelf_spt_id'] = order.shelf_spt_id.id
                        if bool(order.shelf_spt_id.stock_location_id):
                            res['location_dest_id'] = order.shelf_spt_id.stock_location_id.id
                        elif bool(order.storage_spt_id.stock_location_id):
                            res['location_dest_id'] = order.storage_spt_id.stock_location_id.id
                        elif bool(order.location_spt_id.stock_location_id):
                            res['location_dest_id'] = order.location_spt_id.stock_location_id.id
                        picking = StockPicking.sudo().create(res)
                    else:
                        picking = pickings[0]
                    moves = order.order_line._create_stock_moves(picking)
                    moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date):
                        seq += 5
                        move.sequence = seq
                    for move in moves:
                        if move.picking_id.can_send_to_ttr2:
                            MoveToSend |= move
                        else:
                            MoveToAssign |= move
                    MoveToAssign._action_assign()
                    MoveToSend.write({'state': 'waiting'})
                if bool(picking):
                    picking.message_post_with_view('mail.message_origin_link',
                                                   values={'self': picking, 'origin': order},
                                                   subtype_id=self.env.ref('mail.mt_note').id)

        return True

    def update_purchase_on_ttrx(self):
        data = self.from_odoo_to_ttrx()
        purchase_uuid = self.uuid
        if purchase_uuid:
            put_response = None
            try:
                url = f"transactions/purchase/{purchase_uuid}"
                put_response = self.company_id.send_request_to_ttr(
                    request_url=url,
                    request_data=data,
                    method='PUT'
                )
                return put_response
            except Exception as e:
                raise UserError(f'Error: {e}')
        else:
            raise ValueError(f'Error {purchase_uuid} is not a valid uuid.')

    def button_cancel(self):
        res = super(purchase_order, self).button_cancel()
        for reg in self:
            if reg.uuid and reg.connector_id.auto_delete:
                continue
                # raise UserError("Cancellation not possible after transaction to TTRX2")
        return res

    def action_test(self):
        # self.connector_id.crow_get_pick_in()
        self.CreateTTRxPicking()

    def action_recompute(self):
        for order in self:
            order.AfterCreateInTTRx()
            # model = self.env[order._name]
            # # ids = [x.get('id') for x in model.search_read(domain, ['id'])]
            # self.env.all.tocompute[model._fields['picking_ids']].update(order.ids)
            # model.recompute()

    count = fields.Integer(default=1)

    @api.model
    def process_purchase(self, request_data=None, purchase=None, is_create=None, is_delete=None):

        method = 'POST' if is_create else 'PUT'
        method = 'DELETE' if is_delete else method
        url = "/transactions/purchase" if is_create else f"/transactions/purchase/{self.uuid}"
        # request_data = self.name
        request_response = self.company_id.send_request_to_ttr(
            request_url=url,
            request_data=request_data,
            method=method
        )
        if request_response:
            return request_response.get('uuid', "")
        else:
            return

    def _handle_failed_request(self, purchase):
        purchase.write({'state': 'cancel'})
        purchase.unlink()
        raise UserError('Ação não foi processada corretamente em TTRX')

    @api.model
    def create(self, values):
        if not bool(self):
            is_create = True
            created = super().create(values)
            if created:
                request_data = created.from_odoo_to_ttrx()
                # request_data = created.uuid
                post_response = created.process_purchase(request_data, purchase=self, is_create=is_create)
                created.update({'uuid': post_response})
            return created
        # else:
        #     is_create = False
        #     created = super().write(values)
        #     if created:
        #         request_data = created.from_odoo_to_ttrx()
        #         put_response = created.process_purchase(request_data, is_create=is_create)
        #         created.update({'uuid': put_response})
        #     return created

    def write(self, values):
        if self:
            is_create = False
            edited = super(purchase_order, self).write(values)
        if self:
            if edited:
                request_data = self.from_odoo_to_ttrx()
                put_response = self.process_purchase(request_data, is_create=is_create)
        return

    def unlink(self):
        delete_response = self.process_purchase(is_delete=True)
        if delete_response:
            super(purchase_order, self).unlink()
        else:
            super(purchase_order, self).unlink()

    def _get_orders_to_update_from_ttrx(self):
        """ Obtem as linhas da(s) ordem(ns) que ainda não foram
            entregues e informa a ordem para atualizar"""
        line = self.env['purchase.order.line']
        orders = set()
        domain = [('state', 'in', ['purchase']), ('uuid', '!=', False)]
        if bool(self):
            domain += [('order_id', '=', self.id)]
        lines = line.search(domain)
        for line_item in lines:
            if float_compare(line_item.qty_received, line_item.product_qty, precision_digits=0) == (-1):
                orders.add(line_item.order_id.id)
        return orders


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    uuid = fields.Char('UUID from TTR', copy=False)
    status_delete_portal = fields.Boolean(copy=False, index=True)
