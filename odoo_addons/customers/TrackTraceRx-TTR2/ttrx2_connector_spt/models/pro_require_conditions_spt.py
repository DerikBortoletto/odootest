# Ajusted by Alexandre Defendi
from odoo import models, fields, api
from odoo.addons.ttrx2_connector_spt.tools import CleanDataDict, DateTimeToOdoo






class pro_require_conditions_spt(models.Model):
    _name = 'pro.require.conditions.spt'
    _description = 'Product Requirement Conditions'
    
    # create_date = fields.Datetime('Create On') 
    tt_id = fields.Char("TT ID")
    created_on = fields.Datetime('Create On')
    name = fields.Char("Name", required=True)
    requirement_type = fields.Selection([('OWNERSHIP','Ownership'),('STORAGE','Storage')], string="Requirement Type", 
                                        default="OWNERSHIP")
    condition_class = fields.Selection([('LICENSE', 'License'), ('STORAGE_PROPERTY', 'Storage Property')], 
                                       string='Condition Class', required=True, default='LICENSE')
    
    action = fields.Selection([('BUY', 'BUY'),('SELL', 'SELL'),('BOTH', 'BOTH')], string='Action')
    license_type = fields.Many2one('license.types.management.spt', string="Type", copy=False)
    market = fields.Char('Market', )
    country_id = fields.Many2one('res.country', string="Market", help="For LICENSE class only - When is set, the condition will be \
                                                                       enforced only in the specified country. The allowed value is \
                                                                       2 letter ISO country Code.")
    cond_property = fields.Selection([('COLD', 'COLD'),('FROZEN', 'FROZEN'),
                                      ('RESTRICTED_ACCESS', 'RESTRICTED ACCESS')], string='PROPERTY')
    
    product_requirement_id = fields.Many2one('product.requirement.spt', 'Product Requirement')
    connector_id = fields.Many2one('connector.spt', 'Connector')
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)

    # Post
    def _OdooToTTRx(self, values={}):
        license_type_id = values.get('license_type') and self.env['license.types.management.spt'].search(
                                                [('id','=',values['license_type'])],limit=1).lic_id or self.license_type.lic_id
        country_id = values.get('country_id') and self.env['res.country'].search([('id','=',values['country_id'])],limit=1).code or \
                                                                                 self.country_id.code
        product_requirements_id = values.get('product_requirement_id') and self.env['product.requirement.spt'].\
                                  browse(values['product_requirement_id']).tt_id or self.product_requirement_id.tt_id
        var = {
            'id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'product_requirements_id': product_requirements_id,
            'requirement_type': values.get('requirement_type',self.requirement_type),
            'class': values.get('condition_class',self.condition_class),
            'name': values.get('name',self.name),
            'action': values.get('action',self.action),
            'license_type': license_type_id,
            'market': country_id,
            'property': values.get('cond_property',self.cond_property),
        }
        CleanDataDict(var)
        return var

    # Get
    def _TTRxToOdoo(self, values):
        license_type_id = values.get('license_type') and \
                          self.env['license.types.management.spt'].search([('lic_id','=',values['license_type'])],limit=1) or None
        country_id = values.get('market') and self.env['res.country'].search([('code','=',values['market'])],limit=1) or None
        product_requirements_id = values.get('prod_req_id') and self.env['product.requirement.spt'].search(
                                    [('tt_id', '=', values['prod_req_id'])], limit=1).id or None
        
        var = {
            'tt_id': values.get('id'),
            'created_on': DateTimeToOdoo(values['created_on']),
            'name': values.get('name'),
            'condition_class': values.get('class'),
            'action': values.get('action'),
            'license_type': license_type_id,
            'country_id': country_id,
            'cond_property': values.get('property'),
            'product_requirements_id': product_requirements_id,
        }
        CleanDataDict(var)
        return var

    @api.model
    def SyncTTRxProductRequirement(self, connector, prod_req_id):
        response = connector.GetList(self._name, prod_req_id=prod_req_id)
        if bool(response) and bool(response.get('data')):
            for data in response['data']:
                self.CreateUpdateSelf(connector, data['id'], prod_req_id=prod_req_id)
        return True

    def CreateUpdateSelf(self, connector, idx, prod_req_id):
        response = connector.GetRecord(self._name,idx=idx,prod_req_id=prod_req_id)
        if bool(response) and bool(response.get('id')):
            response.update({
                'prod_req_id': prod_req_id,
            })
            data = self._TTRxToOdoo(response)
            data.update({'connector_id': connector.id})
            exist = self.search([('tt_id', '=', data.get('tt_id'))], limit=1)
            if exist:
                context = dict(self.env.context or {})
                context['no_rewrite'] = True
                exist.with_context(context).write(data)
            else:
                exist = self.create(data)
            # Has Joins
        return exist

    @api.model
    def create(self, values):
        res = super(pro_require_conditions_spt, self).create(values)
        for record in res.filtered(lambda x: not x.tt_id):
            request_vals = record._OdooToTTRx()
            create_response = False
            if bool(record.product_category_id.tt_id):
                create_response = record.connector_id.PostRecord(self._name, prod_req_id=record.product_requirement_id.tt_id,
                                                                data=request_vals)
            if bool(create_response) and bool(create_response.get('id')):
                context = dict(self.env.context or {})
                context['no_rewrite'] = True
                record.with_context(context).write({'tt_id': create_response.get('id')})
        return res

    
    
    def write(self, vals):
        if not self.env.context.get('no_rewrite', False):
            for record in self.filtered(lambda x: x.tt_id):
                request_vals = record._OdooToTTRx(vals)
                if bool(record.product_requirement_id.tt_id):
                    record.connector_id.PutRecord(self._name, prod_req_id=record.product_requirement_id.tt_id, 
                                                  idx=record.tt_id, data=request_vals)
        res = super(pro_require_conditions_spt, self).write(vals)
        return res
        
    
    
    def unlink(self):
        if self.company_id.auto_vacuum:
            unlink_ids = self.filtered(lambda x: not x.tt_id)
            for record in self.filtered(lambda x: x.tt_id):
                delete_response = record.connector_id.DeleteRecord(self._name, category_id=record.product_requirement_id.tt_id, 
                                                                   idx=record.tt_id)
                if (bool(delete_response) and bool(delete_response.get('id'))) or (self.user_has_groups('base.group_no_one')):
                    unlink_ids = unlink_ids + record
            return super(pro_require_conditions_spt, unlink_ids).unlink()
        else:
            return super(pro_require_conditions_spt, self).unlink()
