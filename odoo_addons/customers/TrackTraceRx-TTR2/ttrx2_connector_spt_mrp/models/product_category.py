from odoo import models, fields, api
from ..tools import DateTimeToOdoo, CleanDataDict, DateToOdoo



class product_category(models.Model):
    _name = "product.category"
    _inherit = ["custom.connector.spt","product.category"]
    _OdooToTTRx = {'tt_id':'category_id'}
    _TTRxToOdoo = {'id': 'tt_id'}
    _TTRxKey = 'tt_id'
   
    tt_id = fields.Char('TT ID', readonly=True, copy=True)
    created_on = fields.Datetime('Created on', readonly=True)
    code = fields.Char('Code')

    connector_id = fields.Many2one('connector.spt', 'Connector')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, 
                                 default=lambda self: self.env.user.company_id)
    tracktrace_is = fields.Boolean('Is TrackTraceRx2',compute="_compute_tracktrace", store=False)

    product_requirement_ids = fields.Many2many('product.requirement.spt', 'product_requirement_product_category_rel', 
                                               'product_requirement_ids', 'product_category_ids', 'Requirement')
 
    def _compute_tracktrace(self):
        for reg in self:
            reg.tracktrace_is = bool(reg.tt_id)
   
    def FromOdooToTTRx(self, values={}):
        if bool(values):
            parent_category_id = values.get('parent_id') and self.env['product.category'].\
                             search([('id','=',values['parent_id'])],limit=1).tt_id or None
        else:
            parent_category_id = self.parent_id.tt_id
        product_requirements = []
        if not bool(values.get('product_requirement_ids',False)):
            for prod_req in self.product_requirement_ids:
                product_requirements.append(prod_req.tt_id)
        var = {
            'id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'parent_category_id': parent_category_id,
            'code': values.get('code',self.code or None if not bool(values) else None),
            'name': values.get('name',self.name or None if not bool(values) else None),
            'requirements': product_requirements if bool(product_requirements) else None,
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
        parent_id = bool(values.get('parent_category_id')) and self.env['product.category'].\
                    search([('tt_id','=',values['parent_category_id'])],limit=1).id or None
        product_requirement_ids = [(5,),(6,0,values['product_requirement_ids'])] \
                                      if bool(values.get('product_requirement_ids')) else None
        var = {
            'tt_id': values.get('id'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'code': values.get('code'),
            'name': values.get('name'),
            'parent_id': parent_id,
            'product_requirement_ids': product_requirement_ids,
        }
        CleanDataDict(var)
        return var

    def AfterCreateFromTTRx(self, connector, response, data):
        for rec in self.filtered(lambda x: x.tt_id):
            self.env['product.requirement.spt'].SyncFromTTRx(connector,submodal='categories',category_id=rec.tt_id)
    
