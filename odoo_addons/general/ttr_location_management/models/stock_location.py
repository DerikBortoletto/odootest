
from odoo import models, fields, api
from odoo.exceptions import UserError

LOCAL_TYPE = [
    ('main','Main Location'),
    ('sub','Sub Location'),
    ('storage','Storage Area'),
    ('shelf','Storage Shelf'),
]

class StockLocation(models.Model):
    _inherit = 'stock.location'

    def _partner_domain(self):
        if bool(self):
            return [('parent_id','=',self.company_id.partner_id.id)]
        else:
            return [('parent_id','=',self.env.company.partner_id.id)]
    
    def _domain_company_partner_id(self):
        return self._partner_domain()

    location_type = fields.Selection(LOCAL_TYPE, default='main', string="Location Type")
    
    sub_location_ids = fields.One2many('stock.location', 'location_id', string="Sub Location", domain=[('location_type', '=', 'sub')], auto_join=True)
    
    storage_area_ids = fields.One2many('stock.location', 'location_id', string="Storage Area", domain=[('location_type', '=', 'storage')], auto_join=True)

    shelf_name = fields.Char('Shelf Name Prefix')
    storage_shelf_ids = fields.One2many('stock.location', 'location_id', string="Storage Shelf", domain=[('location_type', '=', 'shelf')], auto_join=True)
    
    address_id = fields.Many2one('res.partner', string='Address', domain=lambda self: self._domain_company_partner_id())
    
    @api.onchange('company_id')
    def _onchange_company_id(self):
        domain = self._partner_domain()
        return {'domain': {'address_id': domain}}
    