import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo

_logger = logging.getLogger(__name__)


class product_description_spt(models.Model): #TODO: Rever
    _name = 'product.description.spt'
    _inherit = "custom.connector.spt"
    _description = 'Product Description'
    _OdooToTTRx = {'product_uuid':'product_uuid', 'code': 'description_language_code'}
    _TTRxToOdoo = {'id': 'tt_id'}
    _order = 'code'
    
    tt_id = fields.Char("TTRx id", copy=False, readonly=True)
    code = fields.Char('Language code', copy=False)
    created_on = fields.Datetime('Created on', copy=False)
    last_update = fields.Datetime('Last Update', copy=False)
    name = fields.Char("Name")
    product_long_name = fields.Char("Long Name")
    description = fields.Text("Description")
    composition = fields.Text("Composition")

    product_spt_id = fields.Many2one('product.spt', 'Products')

    traduction_id = fields.Many2one('ir.translation', "Translation")
    product_uuid = fields.Char(compute="_compute_uuid", store=False)
   
    # /products/{product_uuid}/description/{description_language_code}
    def _compute_uuid(self):
        for reg in self:
            reg.product_uuid = reg.product_spt_id.uuid
 
    def FromOdooToTTRx(self, values={}):
        """ From the odoo fields to the TTr2 fields """
         
        var = {
            'language_code': values.get('code',self.code if bool(self.code) else None),
            'last_update': values.get('last_update',str(self.last_update) or None if not bool(values) else None),
            'name': values.get('name',self.name or None if not bool(values) else None),
            'description': values.get('description',self.description or None if not bool(values) else None),
            'composition': values.get('composition',self.composition or None if not bool(values) else None),
            'product_long_name': values.get('product_long_name',self.product_long_name or None if not bool(values) else None),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
        """ From the TTr2 fields to the Odoo fields """
        product_spt_id = bool(values.get('product_spt_id')) and self.env['product.spt'].\
                              search([('uuid','=',values['product_spt_id'])],limit=1).id or None
        var = {
            'code': values.get('language_code'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': values.get('name'),
            'description': values.get('description'),
            'composition': values.get('composition'),
            'product_long_name': values.get('product_long_name'),
            'product_spt_id': product_spt_id,
        }
        CleanDataDict(var)
        return var
    
 
    
