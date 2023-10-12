import json
import logging
import urllib.error
import urllib.request as urllib2
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

READ_STATE={'draft': [('readonly', False)]}


class SyncManufacturerSptWizard(models.TransientModel):
    _name = 'sync.manufacturer.spt.wizard'
    _description = 'Product Sync Wizard'
    
    connector_id = fields.Many2one('connector.spt', 'Connector', required=True, readonly=True)
    
    sync_type = fields.Selection([('send','Send'),('receive','Receive'),('both','Send & Receive')], string='Sync', 
                                 required=True, default='receive', readonly=True, states=READ_STATE)
    from_type = fields.Selection([('all','All'), ('date','a Date')], string='Since', required=True, default='all', readonly=True, 
                                 states=READ_STATE)
    from_date = fields.Date(string='From', default=fields.Date.context_today, readonly=True, states=READ_STATE)
    
    # from_categ_ids = fields.Many2many(comodel_name="product.category", string="Categories", readonly=True, states=READ_STATE)
    # from_manufacturer_ids = fields.Many2many(comodel_name="manufacturers.spt", string="Manufacturers", readonly=True, states=READ_STATE)


    # Include
    # category = fields.Boolean('Categories', default=True, readonly=True, states=READ_STATE)
    # packsize = fields.Boolean('Pack Sizes', default=True, readonly=True, states=READ_STATE)
    
    total_imported = fields.Integer('Amount Process', readonly=True)
    notes_process = fields.Text('Notes of Process', readonly=True)
    
    state = fields.Selection([('draft','Start'),('done','Done')], default='draft')
    
    
    def action_process(self):
        for record in self:
            total = 0
            # if self.sync_type == 'date':
            # if self.category:
            #     self.env['product.category'].SyncTTRx(record.connector_id)
            # if self.packsize:
            #     self.env['pack.size.type.spt'].SyncTTRx(record.connector_id)
            self.env['manufacturers.spt'].SyncFromTTRx(record.connector_id)
            record.total_imported = total
            record.state = 'done'
            record.notes_process = "Successfully processed"
        return {  # Recarrega a view após a importação para mostrar resultados
                "type": "ir.actions.act_window",
                "res_model": "sync.product.spt.wizard",
                "views": [[False, "form"]],
                "name": "Sync Products",
                "target": "new",
                "res_id": self.id,
        }
            
            
            