from odoo import models, fields





class pro_require_owner_conditions_spt(models.Model):
    _name = 'pro.require.owner.conditions.spt'
    _description = 'Product Requirement Ownership Conditions'
    
    # create_date = fields.Datetime('Create On') 
    name = fields.Char("Name")
    cond_property = fields.Selection([
        ('cold', 'COLD'),
        ('fronzen', 'FROZEN'),
        ('restricted_access', 'RESTRICTED ACCESS')], string='PROPERTY')
    product_requirement_ids = fields.Many2one('product.requirement.spt', 'Product Requirement')
