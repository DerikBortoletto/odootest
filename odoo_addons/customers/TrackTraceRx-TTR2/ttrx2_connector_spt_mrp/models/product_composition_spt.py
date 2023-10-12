# Ajusted by Alexandre Defendi
from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo





class product_composition_spt(models.Model): #TODO: Rever
    _name = 'product.composition.spt'
    _inherit = "custom.connector.spt"
    _description = 'Product Composition'
    _rec_name = 'product_spt_id'
    _TTRxKey = 'product_uuid,child_product_uuid'
    _OdooToTTRx = {'product_uuid': 'product_uuid', 'child_product_uuid':'child_product_uuid'}
    _TTRxToOdoo = {'product_uuid': 'product_uuid', 'child_product_uuid':'child_product_uuid', 'uuid':'child_product_uuid'}
    
    #TODO: Add BoM
    # uuid = fields.Char("UUID", copy=False)
    product_uuid = fields.Char('Product UUID')
    product_spt_id = fields.Many2one('product.spt', 'Compose', copy=False, required=True)
    child_product_uuid = fields.Char('Product Child UUID')
    child_product_spt_id = fields.Many2one('product.spt', 'Composition', copy=False)
    quantity = fields.Integer('Quantity')
    parent_id = fields.Many2one('product.composition.spt', 'Parent Composition')
    child_ids = fields.One2many('product.composition.spt', 'parent_id', 'Child Compositions')
    
    
    def FromOdooToTTRx(self, values={}):
        """ From the odoo fields to the TTr2 fields """
        var = {
            'product_uuid': values.get('product_uuid',self.product_uuid),
            'child_product_uuid': values.get('child_product_uuid',self.child_product_uuid),
            'quantity': values.get('quantity',self.quantity),
        }
        CleanDataDict(var)
        return var



    def FromTTRxToOdoo(self, values):
        """ From the TTr2 fields to the Odoo fields """

        product_spt_id = values.get('product_uuid') and self.env['product.spt'].search([('uuid','=',values['product_uuid'])],
                                                                                           limit=1).id or None
        child_product_spt_id = values.get('child_product_uuid') and self.env['product.spt'].search([('uuid','=',values['child_product_uuid'])], 
                                                                                             limit=1).id or None
        var = {
            'product_uuid': values.get('product_uuid'),
            'product_spt_id': product_spt_id,
            'child_product_uuid': values.get('child_product_uuid'),
            'child_product_spt_id': child_product_spt_id,
            'quantity': values.get('quantity'),
        }
        CleanDataDict(var)
        return var

    def BeforeCreateFromTTRx(self, connector, response, data):
        if not bool(data.get('product_spt_id')) and bool(response.get('product_uuid')):
            data['product_spt_id'] = self.env['product.spt'].SyncFromTTRx(connector, product_uuid=response['product_uuid']).id
                                                     
        if not bool(data.get('child_product_spt_id')) and bool(response.get('child_product_uuid')):
            data['child_product_spt_id'] = self.env['product.spt'].SyncFromTTRx(connector, product_uuid=response['child_product_uuid']).id

    @api.model
    def create(self, values):
        return super().create(values)

