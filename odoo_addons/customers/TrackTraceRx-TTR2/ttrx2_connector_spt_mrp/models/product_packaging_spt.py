from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo





class product_packaging_spt(models.Model):
    _name = 'product.packaging.spt'
    _inherit = "custom.connector.spt"
    _description = 'Product Packaging'
    _OdooToTTRx = {'product_uuid':'product_uuid', 'ttr_uuid': 'uuid'}
    _TTRxToOdoo = {'uuid': 'ttr_uuid'}
    _TTRxKey = 'ttr_uuid'
    _order = 'name'
    
    ttr_uuid = fields.Char("UUID", copy=False)
    created_on = fields.Datetime('Create On', copy=False)
    last_update = fields.Datetime('Last Update', copy=False)
    name = fields.Char("Name", required=True)
    active = fields.Boolean("Active", default=True, copy=False)

    product_spt_id = fields.Many2one('product.spt', 'Product spt')

    packaging_layers_ids = fields.One2many('product.packaging.layers.spt','packaging_spt_id', string='Product Packaging Layers')

    product_uuid = fields.Char(compute="_compute_uuid", store=False)
    
    def _compute_uuid(self):
        for reg in self:
            reg.product_uuid = reg.product_spt_id.uuid
 
    def FromOdooToTTRx(self, values={}):
        """ From the odoo fields to the TTr2 fields """
         
        var = {
            'uuid': values.get('ttr_uuid',self.ttr_uuid if bool(self.ttr_uuid) else None),
            'name': values.get('name',self.name or None if not bool(values) else None),
            'is_active': values.get('active',self.active or None if not bool(values) else None),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
        """ From the TTr2 fields to the Odoo fields """
        var = {
            'ttr_uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values['created_on']['date']),
            'last_update': DateTimeToOdoo(values['last_update']['date']),
            'name': values.get('name'),
            'code': values.get('identifier_code'),
            'identifier_value': values.get('value'),
            'product_spt_id': values.get('product_spt_id'),
        }
        CleanDataDict(var)
        return var

    def BeforeCreateFromTTRx(self, connector, response, data):
        if bool(response.get('product_uuid')):
            data['product_spt_id'] = self.env['product.spt'].SyncFromTTRx(connector,uuid=response['product_uuid'],update=False).id
        return True
    

    def AfterCreateFromTTRx(self, connector, response, data):
        self.env['product.packaging.layers.spt'].SyncFromTTRx(connector, product_uuid=self.product_spt_id.uuid, 
                                                              packaging_uuid=self.ttr_uuid)
    
