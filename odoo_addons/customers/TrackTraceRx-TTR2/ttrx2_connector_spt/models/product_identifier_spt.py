import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo

_logger = logging.getLogger(__name__)


# IDENT_CODES = [
#     ('us_ndc', 'NDC - National Drug Code (US)'),
#     ('ca_din', 'DIN - Drug Identification Number (CA)'),
#     ('custom', 'Custom'),
#     ('us_ndc442', 'NDC - National Drug Code (4-4-2) (US)'),
#     ('us_ndc532', 'NDC - National Drug Code (5-3-2) (US)'),
#     ('us_ndc542', 'NDC - National Drug Code (5-4-2) (US)'),
#     ('us_ndc541', 'NDC - National Drug Code (5-4-1) (US)'),
#     ('material_code', 'Material Code'),
#     ('br_anvisa', 'Registro Anvisa (BR)')
# ]

class identifiers_types_spt(models.Model):
    _name = 'identifiers.types.spt'
    _inherit = "custom.connector.spt"
    _description = "List of Product Identifiers for the given product"
    _TTRxKey = 'code'
    _order = 'name'
    _OdooToTTRx = {'code':'code'}
    
    code = fields.Char('Code')
    name = fields.Char('Name')

    def FromTTRxToOdoo(self, connector, values):
        var = {
            'code': values.get('code'),
            'name': values.get('name'),
        }
        CleanDataDict(var)
        return var

class product_identifier_spt(models.Model):
    _name = 'product.identifier.spt'
    _inherit = "custom.connector.spt"
    _description = 'Product Identifier'
    _OdooToTTRx = {'product_uuid':'product_uuid', 'tt_id': 'id'}
    _TTRxToOdoo = {'id': 'tt_id'}
    _TTRxKey = 'tt_id'
    _order = 'name'
    
    tt_id = fields.Char('TTRx ID', copy=False, readonly=True)
    created_on = fields.Datetime('Create on', copy=False, readonly=True)
    last_update = fields.Datetime('Last Update on', copy=False, readonly=True)
    name = fields.Many2one('identifiers.types.spt', 'Identifier Code', required=True, copy=False)
    identifier_value = fields.Char("Identifier Value")
    product_spt_id = fields.Many2one('product.spt', 'Product', required=True)

    
    _sql_constraints = [
        ('unique_product_identifier_id', 'unique (product_spt_id,name)', 'One product can not have same two requirement type.!!! ')
    ]
    
    def FromOdooToTTRx(self, connector, values={}):
        """ From the odoo fields to the TTr2 fields """
        product_uuid = values.get('product_spt_id') and self.env['product.spt'].browse(values['product_spt_id']).uuid or self.product_spt_id.uuid
        identifier_code = values.get('name') and self.env['identifiers.types.spt'].browse(values['name']).code or self.name.code
        var = {
            'identifier_id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'identifier_code': identifier_code,
            'value': values.get('identifier_value',self.identifier_value),
            'product_uuid': product_uuid,
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        """ From the TTr2 fields to the Odoo fields """
        product_spt_id = values.get('product_uuid') and self.env['product.spt'].search([('uuid','=',values['product_uuid'])],limit=1).id or None
        identifier_code = values.get('identifier_code') and self.env['identifiers.types.spt'].search([('code','=',values['identifier_code'])],limit=1).id or None
        # print("Product Identifier ", values)
        var = {
            'tt_id': values.get('id'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': identifier_code,
            'identifier_value': values.get('value'),
            'product_spt_id': product_spt_id,
        }
        CleanDataDict(var)
        return var
 
    def BeforeCreateFromTTRx(self, connector, response, data):
        if bool(response.get('product_uuid')):
            data['product_spt_id'] = self.env['product.spt'].SyncFromTTRx(connector,uuid=response['product_uuid'],update=False).id
        return True
   
