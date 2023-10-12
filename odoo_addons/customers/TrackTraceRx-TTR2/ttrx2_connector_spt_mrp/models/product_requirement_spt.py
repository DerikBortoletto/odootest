# Ajusted by Alexandre Defendi
from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo





class product_requirement_spt(models.Model):
    _name = 'product.requirement.spt'
    _inherit = "custom.connector.spt"
    _description = 'Product Requirement'
    _OdooToTTRx = {'tt_id':'product_require_id'}
    _TTRxToOdoo = {'id':'tt_id'}
    _TTRxKey = 'tt_id'
    _order = 'name'
    
    tt_id = fields.Char("TTRx id", copy=False, readonly=True)
    created_on = fields.Datetime('Created on')
    type = fields.Selection([('SCHEDULE', 'Schedule'), ('COMMERCIAL', 'Commercial')], string='Type', required=True)
    product_class = fields.Selection([('pharmaceutical', 'Pharmaceutical'),
                                      ('shoes', 'Shoe')], default="pharmaceutical", string='Product Type')
    name = fields.Char("Name", required=True)
    
    
    # Joins
    # product_category_id = fields.Many2one('product.category', 'Product Category')
    # product_template_id = fields.Many2one('product.template', 'Products')

    pro_require_lic_conditions_ids = fields.One2many('pro.require.conditions.spt', 'product_requirement_id',
                                                     'Product Requirement License Conditions',
                                                     domain=[('condition_class', '=', 'LICENSE')])
    pro_require_owner_conditions_ids = fields.One2many('pro.require.conditions.spt', 'product_requirement_id',
                                                       'Product Requirement Ownership Conditions',
                                                       domain=[('condition_class', '=', 'STORAGE_PROPERTY')])
   
    def FromOdooToTTRx(self, values={}):
        """ From the odoo fields to the TTr2 fields """
        var = {
            'product_requirements_id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'type': values.get('name',self.type),
            'product_class': values.get('product_class',self.product_class),
            'name': values.get('name',self.name),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
        """ From the TTr2 fields to the Odoo fields """
        product_category_id = bool(values.get('product_category_id')) and self.env['product.category'].search([('tt_id','=',
                                                                            values['product_category_id'])],limit=1).id or None
        pro_require_lic_conditions_ids = [(5),(6,0,values['pro_require_lic_conditions_ids'])] \
                                         if bool(values.get('pro_require_lic_conditions_ids')) else None
        pro_require_owner_conditions_ids = [(5),(6,0,values['pro_require_owner_conditions_ids'])] \
                                         if bool(values.get('pro_require_owner_conditions_ids')) else None
        var = {
            'tt_id': values.get('id'),
            'name': values.get('name'),
            'created_on': DateTimeToOdoo(values['created_on']) if bool(values.get('created_on')) else None,
            'type': values.get('type'),
            'product_class': values.get('product_class'),
            'product_category_id': product_category_id,
            'pro_require_lic_conditions_ids': pro_require_lic_conditions_ids,
            'pro_require_owner_conditions_ids': pro_require_owner_conditions_ids,
        }
        CleanDataDict(var)
        return var

    def AfterCreateFromTTRx(self, connector, response, data):
        self.env['pro.require.conditions.spt'].SyncFromTTRx(connector, prod_req_id=self.tt_id)
          
    def action_send(self):
        for reg in self:
            reg.CreateInTTRx()
        return True

    def action_refresh(self):
        for reg in self:
            reg.SyncFromTTRx(self.connector_id,myown=True)
        return True

    def action_test(self):
        pass
        
        