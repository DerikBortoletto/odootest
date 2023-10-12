from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo


PKG_SERIALIZATION_TYPE = [
    ('NO_SERIALIZATION','No Serialization'),
    ('SEQUENTIAL', 'Sequential'),
    ('RANDOM', 'Randomic'),
]

PKG_CODE_TYPE =[
    ('GTIN12','GTin12'),
    ('GTIN13','GTin13'),
    ('GTIN14','GTin14'),
    ('NTIN','NTin'),
]

class product_packaging_layers_spt(models.Model):
    _name = 'product.packaging.layers.spt'
    _inherit = "custom.connector.spt"
    _description = 'Product Packaging Layers'
    _inherits = {'product.packaging': 'packaging_id'}
    _OdooToTTRx = {'product_uuid':'product_uuid', 'packaging_uuid': 'packaging_uuid', 'ttr_id': 'id'}
    _TTRxToOdoo = {'id': 'ttr_id'}
    _TTRxKey = 'ttr_id'

    packaging_id = fields.Many2one('product.packaging', 'Packaging', auto_join=True, index=True, ondelete="cascade", required=True)

    ttr_id = fields.Char("UUID", copy=False)
    created_on = fields.Datetime('Create On', copy=False)
    last_update = fields.Datetime('Last Update', copy=False)
    quantity = fields.Integer('Quantity', copy=False)
    code_type = fields.Selection(PKG_CODE_TYPE, string="Code Type")
    code_value = fields.Char('Code Value')
    gs1_company_prefix = fields.Char('GS1 Prefix')
    serialization_type = fields.Selection(PKG_SERIALIZATION_TYPE, string='Serialization')
    is_require_aggregation = fields.Boolean('Require Aggregation')
    
    
    product_spt_id = fields.Many2one('product.spt', 'Product', required=True)
    packaging_spt_id = fields.Many2one('product.packaging.spt', 'Packaging', required=True)
    packaging_type_id = fields.Many2one('pack.size.type.spt', string='Packaging Type', required=True)
    parent_id = fields.Many2one('product.packaging.layers.spt', string='Parent')
    
    product_uuid = fields.Char(compute="_compute_uuid", store=False)
    packaging_uuid = fields.Char(compute="_compute_uuid", store=False)
    
    def _compute_uuid(self):
        for reg in self:
            reg.product_uuid = reg.product_spt_id.uuid
            reg.packaging_uuid = reg.packaging_spt_id.uuid
 
    
    def FromOdooToTTRx(self, connector, values={}):
        """ From the odoo fields to the TTr2 fields """
        product_uuid = values.get('product_spt_id') and \
                       self.env['product.spt'].brownse([values['product_spt_id']]).uuid or self.product_spt_id.uuid
        packaging_uuid = values.get('packaging_spt_id') and \
                         self.env['product.packaging.spt'].brownse([values['packaging_spt_id']]).uuid or self.packaging_spt_id.uuid
        packaging_type_id = values.get('packaging_type_id') and \
                            self.env['pack.size.type.spt'].brownse([values['packaging_type_id']],limit=1).tt_id or self.packaging_type_id.tt_id
        parent_layer_id = values.get('parent_id') and \
                          self.env['product.packaging.layers.spt'].brownse([values['parent_id']]).ttr_id or self.parent_id.ttr_id
            
        var = {
            'layer_id': values.get('ttr_id',self.ttr_id if bool(self.ttr_id) else None),
            'product_uuid': product_uuid,
            'packaging_uuid': packaging_uuid,
            'packaging_type_id': packaging_type_id,
            'parent_layer_id': parent_layer_id,
            'quantity': values.get('qty',self.qty if not bool(values) else None),
            'code_type': values.get('code_type',self.code_type or None if not bool(values) else None),
            'code_value': values.get('barcode',self.barcode or None if not bool(values) else None),
            'gs1_company_prefix': values.get('gs1_company_prefix',self.gs1_company_prefix or None if not bool(values) else None),
            'serialization_type': values.get('serialization_type',self.serialization_type or None if not bool(values) else None),
            'is_require_aggregation': values.get('is_require_aggregation',self.is_require_aggregation if not bool(values) else None),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        """ From the TTr2 fields to the Odoo fields """
        product_spt_id = values.get('product_uuid') and self.env['product.spt'].search([('uuid','=',values['product_uuid'])],
                                                                                       limit=1).id or None 
        packaging_spt = values.get('packaging_uuid') and self.env['product.packaging.spt'].search(
                        [('uuid','=',values['packaging_uuid'])],limit=1)
        packaging_type_id = values.get('packaging_type') and values['packaging_type'].get('id') and \
                            self.env['pack.size.type.spt'].search([('tt_id','=',values['packaging_type']['id'])],limit=1).id or None
        parent_id = None
        # print("Product Packaging Layer ", values)
        var = {
            'ttr_id': values.get('id'),
            'name': packaging_spt.name or None,
            'created_on': DateTimeToOdoo(values['created_on']['date'] if bool(values.get('created_on')) else None),
            'last_update': DateTimeToOdoo(values['last_update']['date'] if bool(values.get('last_update')) else None),
            'product_spt_id': product_spt_id,
            'packaging_spt_id': packaging_spt.id or None,
            'packaging_type_id': packaging_type_id,
            'parent_id': parent_id,
            'qty': values.get('quantity'),
            'code_type': values.get('code_type'),
            'barcode': values.get('code_value'),
            'gs1_company_prefix': values.get('gs1_company_prefix'),
            'serialization_type': values.get('serialization_type'),
            'is_require_aggregation': values.get('is_require_aggregation'),
        }
        CleanDataDict(var)
        return var
    
