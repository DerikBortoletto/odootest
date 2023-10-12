# Ajusted by Alexandre Defendi
from odoo import models, fields, api
from odoo.addons.tracktrace2_odoo_connector_spt.tools import CleanDataDict, DateTimeToOdoo






class pro_require_conditions_spt(models.Model):
    _name = 'pro.require.conditions.spt'
    _inherit = "custom.connector.spt"
    _description = 'Product Requirement Conditions'
    _OdooToTTRx = {'prod_req_id': 'prod_req_id', 'tt_id':'id'}
    _TTRxToOdoo = {'id': 'tt_id'}
    _TTRxKey = 'tt_id'
    _order = 'name'
    
    tt_id = fields.Char("TT ID", readonly=True, copy=False)
    created_on = fields.Datetime('Create On', readonly=True)
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

    is_validate_trading_partner_license_in_po = fields.Boolean(string='Is validate license of partner in purchase')
    is_validate_location_license_in_po = fields.Boolean(string='Is validate license of location in purchase')
    is_validate_trading_partner_license_in_so = fields.Boolean(string='Is validate license of partner in sale')
    is_validate_location_license_in_so = fields.Boolean(string='Is validate license of location in sale')
    
    product_requirement_id = fields.Many2one('product.requirement.spt', 'Product Requirement')
    prod_req_id = fields.Char(compute="_compute_uuid", store=False)

    def _compute_uuid(self):
        for reg in self:
            reg.prod_req_id = reg.product_requirement_id.tt_id

    # Post
    def FromOdooToTTRx(self, values={}):
        license_type_id = values.get('license_type') and self.env['license.types.management.spt'].search(
                                                [('id','=',values['license_type'])],limit=1).lic_id or self.license_type.lic_id
        country_id = values.get('country_id') and self.env['res.country'].search([('id','=',values['country_id'])],
                                                                                 limit=1).code or self.country_id.code
        product_requirements_id = values.get('product_requirement_id') and self.env['product.requirement.spt'].\
                                  browse(values['product_requirement_id']).tt_id or self.product_requirement_id.tt_id
            
        var = {
            'id': values.get('tt_id',self.tt_id if bool(self.tt_id) else None),
            'product_requirements_id': product_requirements_id,
            'requirement_type': values.get('requirement_type',self.requirement_type),
            'class': values.get('condition_class',self.condition_class),
            'name': values.get('name',self.name),
            'action': values.get('action',self.action),
            'license_type_id': license_type_id,
            'is_validate_trading_partner_license_in_po': values.get('is_validate_trading_partner_license_in_po',
                                                                    self.is_validate_trading_partner_license_in_po),
            'is_validate_location_license_in_po': values.get('is_validate_location_license_in_po',
                                                             self.is_validate_location_license_in_po),
            'is_validate_trading_partner_license_in_so': values.get('is_validate_trading_partner_license_in_so',
                                                                    self.is_validate_trading_partner_license_in_so),
            'is_validate_location_license_in_so': values.get('is_validate_location_license_in_so',
                                                             self.is_validate_location_license_in_so),
            'market': country_id,
            'property': values.get('cond_property',self.cond_property),
        }
        CleanDataDict(var)
        return var

    # Get
    def FromTTRxToOdoo(self, values):
        license_type_id = values.get('license_type') and \
                          self.env['license.types.management.spt'].search([('lic_id','=',values['license_type'])],limit=1) or None
        country_id = values.get('market') and self.env['res.country'].search([('code','=',values['market'])],limit=1) or None
        product_requirements_id = values.get('prod_req_id') and self.env['product.requirement.spt'].search(
                                    [('tt_id', '=', values['prod_req_id'])], limit=1).id or None
        
        var = {
            'tt_id': values.get('id'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'name': values.get('name'),
            'condition_class': values.get('class'),
            'action': values.get('action'),
            'license_type': license_type_id,
            'country_id': country_id,
            'cond_property': values.get('property'),
            'product_requirements_id': product_requirements_id,
            'is_validate_trading_partner_license_in_po': values.get('is_validate_trading_partner_license_in_po'),
            'is_validate_location_license_in_po': values.get('is_validate_location_license_in_po'),
            'is_validate_trading_partner_license_in_so': values.get('is_validate_trading_partner_license_in_so'),
            'is_validate_location_license_in_so': values.get('is_validate_location_license_in_so'),
        }
        CleanDataDict(var)
        return var

