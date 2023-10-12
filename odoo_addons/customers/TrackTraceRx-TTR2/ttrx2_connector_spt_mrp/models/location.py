from odoo import models, fields, api
from odoo.exceptions import UserError

class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    tracktrace_is = fields.Boolean('Is TrackTraceRx2',compute="_compute_tracktrace", readonly=True, store=False)
    location_spt_id = fields.Many2one('locations.management.spt',string='Location SPT',compute="_compute_tracktrace", readonly=True, store=False)
    storage_area_spt_id = fields.Many2one('storage.areas.spt',string='Storage Area SPT',compute="_compute_tracktrace", readonly=True, store=False)
    storage_shelf_spt_id = fields.Many2one('shelf.spt',string='Storage Shelf SPT',compute="_compute_tracktrace", readonly=True, store=False)

    def _parent_location(self):
        location_spt_id = self.env['locations.management.spt'].search([('stock_location_id','=',self.id)],limit=1)
        while not bool(location_spt_id):
            
            location_spt_id = location_spt_id.search([('stock_location_id','=',self.id)],limit=1)
            
        
        self.env['locations.management.spt'].search([('stock_location_id','=',self.id)],limit=1)
    
    def _compute_tracktrace(self):
        for reg in self:
            reg.storage_shelf_spt_id = self.env['shelf.spt'].search([('stock_location_id','=',reg.id)],limit=1)
            if bool(reg.storage_shelf_spt_id.location_id):
                reg.storage_area_spt_id = self.env['storage.areas.spt'].search([('stock_location_id','=',
                                                                                 reg.storage_shelf_spt_id.location_id.id)],limit=1)
            else:
                reg.storage_area_spt_id = self.env['storage.areas.spt'].search([('stock_location_id','=',reg.id)],limit=1)
            
            if bool(reg.storage_area_spt_id):
                storage_id = reg.storage_area_spt_id
                location_spt_id = self.env['locations.management.spt'].search([('stock_location_id','=',
                                                                                storage_id.location_id.id)],limit=1)
                while not bool(location_spt_id):
                    storage_id = self.env['storage.areas.spt'].search([('location_id','=',
                                                                                 storage_id.location_id.id)],limit=1)
                    if bool(storage_id):
                        location_spt_id = self.env['locations.management.spt'].search([('stock_location_id','=',
                                                                                storage_id.location_id.id)],limit=1)
                    else:
                        location_spt_id = self.env['locations.management.spt']
                        break
                reg.location_spt_id = location_spt_id
            else:
                reg.location_spt_id = self.env['locations.management.spt'].search([('stock_location_id','=',reg.id)],limit=1)
            
            reg.tracktrace_is = bool(reg.location_spt_id) or bool(reg.storage_area_spt_id) or bool(reg.storage_shelf_spt_id)
