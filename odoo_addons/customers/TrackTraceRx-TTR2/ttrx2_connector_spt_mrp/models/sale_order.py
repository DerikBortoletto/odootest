import json
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from ..tools import DateTimeToOdoo, CleanDataDict

_logger = logging.getLogger(__name__)









class sale_order(models.Model):
    _name = 'sale.order'
    _inherit = ["custom.connector.spt","sale.order"]
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'uuid':'uuid'}
    _TTRxToOdoo = {'uuid':'uuid'}
    
    uuid = fields.Char("UUID", copy=False)
    source_location = fields.Many2one('stock.location', string="Source Location") #TODO: Verificar
    send_to_ttr2 = fields.Boolean('Send to TTRx', default=False)
    
    def FromOdooToTTRx(self, values={}):
        var = super().FromOdooToTTRx(values=values)

        #TODO: Tratamento quando o partner nao for da TTRx
        if not bool(self.partner_id.uuid):
            partner_uuid = self.partner_id.CreateInTTRx()
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
                #TODO: Tratamento de quando o produto nao estiver na TTRx
                raise UserError("Product " + line.product_id.name + " does not exist in TTR system.")

        if not self.source_location.location_spt_id.uuid:
            #TODO: Tratamento de quando o default location não estiver na TTRx
            raise UserError("Location " + self.source_location.name + " does not exist in TTR system.")
        else:
            location_uuid = self.source_location.location_spt_id.uuid

        var.update({
            "transaction_type": "sales",
            "location_uuid": location_uuid,
            "trading_partner_uuid": partner_uuid,
            "transaction_date": str(self.date_order.date()),
            "po_nbr": str(self.name),
            "line_items": json.dumps(item_lines),
            "sold_by_address_custom_recipient_name": self.company_id.name,
            "sold_by_address_custom_line1": self.company_id.street or None,
            "sold_by_address_custom_line2": self.company_id.street2 or None,
            "sold_by_address_custom_country_code": self.company_id.country_id.code or None,
            "sold_by_address_custom_country_name": self.company_id.country_id.name or None,
            "sold_by_address_custom_city": self.company_id.city or None,
            "sold_by_address_custom_zip": self.company_id.zip or None,
            "sold_by_address_custom_phone": self.company_id.phone or None,
            "sold_by_address_custom_email": self.company_id.email or None,
            "ship_from_address_custom_recipient_name": self.company_id.name,
            "ship_from_address_custom_line1": self.company_id.street or None,
            "ship_from_address_custom_line2": self.company_id.street2 or None,
            "ship_from_address_custom_country_code": self.company_id.country_id.code or None,
            "ship_from_address_custom_country_name": self.company_id.country_id.name or None,
            "ship_from_address_custom_city": self.company_id.city or None,
            "ship_from_address_custom_zip": self.company_id.zip or None,
            "ship_from_address_custom_phone": self.company_id.phone or None,
            "ship_from_address_custom_email": self.company_id.email or None,
            "billing_address_custom_recipient_name": self.partner_id.name,
            "billing_address_custom_line1": self.partner_id.street or None,
            "billing_address_custom_line2": self.partner_id.street2 or None,
            "billing_address_custom_country_code": self.partner_id.country_id.code or None,
            "billing_address_custom_country_name": self.partner_id.country_id.name or None,
            "billing_address_custom_city": self.partner_id.city or None,
            "billing_address_custom_zip": self.partner_id.zip or None,
            "billing_address_custom_phone": self.partner_id.phone or None,
            "billing_address_custom_email": self.partner_id.email or None,
            "ship_to_address_custom_recipient_name": self.partner_id.name,
            "ship_to_address_custom_line1": self.partner_id.street or None,
            "ship_to_address_custom_line2": self.partner_id.street2 or None,
            "ship_to_address_custom_country_code": self.partner_id.country_id.code or None,
            "ship_to_address_custom_country_name": self.partner_id.country_id.name or None,
            "ship_to_address_custom_city": self.partner_id.city or None,
            "ship_to_address_custom_zip": self.partner_id.zip or None,
            "ship_to_address_custom_phone": self.partner_id.phone or None,
            "ship_to_address_custom_email": self.partner_id.email or None,
            "is_approved": True,
            # "is_approved_is_ship_transaction": True,
        })
        CleanDataDict(var)
        return var
    
    def FromTTRxToOdoo(self, values):
        var = super().FromTTRxToOdoo(values=values)
        order_lines = self.FromLinesTTRxToOdoo(values['line_items'])
        new_order_lines = []
        if self.search_count([('uuid','=',values['uuid'])]) > 0:
            for line in order_lines:
                nid = line.pop('id')
                new_order_lines += [(1,nid,line)]
        else:
            new_order_lines += [(5,)]
            for line in order_lines:
                line.pop('id')
                new_order_lines += [(0,0,line)]

        var.update({
            'order_line': new_order_lines,
        })
        CleanDataDict(var)
        return var

    def FromLinesTTRxToOdoo(self, ttr_lines):
        order_line = []
        for ttr_line in ttr_lines:
            product_uuid = ttr_line['product']['uuid']
            product_id = self.env['product.spt'].search([('uuid','=',product_uuid)],limit=1).product_id
            var = {
                'uuid': ttr_line.get('uuid'),
                'product_id': product_id.id,
                'product_uom': product_id.uom_id.id,
                'name': product_id.name,
                'product_uom_qty': ttr_line.get('quantity'),
                'id': int(ttr_line['sort_order']) if bool(ttr_line.get('sort_order')) else None,
            }
            CleanDataDict(var)
            order_line.append(var)
        return order_line
        
    


    def CreateInTTRx(self, **params):
        resource = "%s" % self._name
        params['data'] = self.FromOdooToTTRx()
        if bool(self.BeforeCreateInOdoo(**params)):
            create_response = self._PostRecord(self.connector_id, resource, **params) 
            if bool(create_response) and not bool(create_response.get('erro')):
                context = dict(self.env.context or {})
                context['no_rewrite'] = True
                self.with_context(context).write(create_response)
                response, data = self.env['sale.order'].GetValuesInTTRx(self.connector_id,uuid=create_response['uuid'])
                order_line = []
                for line in data['order_line']:
                    order_line += [(1,line[1],{'uuid': line[2]['uuid']})]
                self.with_context(context).write({'order_line': order_line})
                
            self.AfterCreateInOdoo(**params)
        return True


    def DeleteInTTRx(self, **params):
        self.ensure_one
        if self.uuid:
            res = {'erro': 'Delete is not possible after transaction to TTRX2'}
        return res
    
    
    
    
    
    
    def action_confirm(self):
        res = super(sale_order, self).action_confirm()
        for record in self:
            record.CreateInTTRx()
        return res
    
    
    
    @api.model
    def create(self, values):
        if 'order_line' in values:
            res = super(sale_order, self).create(values)
            return res
        else:
            raise ValidationError('Order Line is not Selected.')
    
    
    
    
    def write(self, values):
        res = super(sale_order, self).write(values)
        if len(self.order_line) == 0:
            raise ValidationError('Order Line is not Selected.')
        else:
            return res

    # TTRX2 not support delete sales order so we disabled the process.
    def action_cancel(self):
        res = super(sale_order, self).action_cancel()
        for reg in self:
            if reg.uuid:
                raise UserError("Cancellation not possible after transaction to TTRX2")
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    uuid = fields.Char('UUID from TTR', copy=False, readonly=True)
