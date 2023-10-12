import json
import logging
import urllib.error
import urllib.request as urllib2
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

READ_STATE={'draft': [('readonly', False)]}


class SyncPartnerSptWizard(models.TransientModel):
    _name = 'sync.partner.spt.wizard'
    _description = 'Partner Sync Wizard'
    
    connector_id = fields.Many2one('connector.spt', 'Connector', required=True, readonly=True)
    
    sync_type = fields.Selection([('send','Send'),('receive','Receive'),('both','Send & Receive')], string='Sync', 
                                 required=True, default='receive', readonly=True, states=READ_STATE)
    from_type = fields.Selection([('all','All'), ('date','a Date')], string='Since', required=True, default='all', readonly=True, 
                                 states=READ_STATE)
    from_date = fields.Date(string='From', default=fields.Date.context_today, readonly=True, states=READ_STATE)

    # Include
    partners = fields.Boolean('Trade Partners', default=True, readonly=True, states=READ_STATE)
    license_type = fields.Boolean('License Type', default=True, readonly=True, states=READ_STATE)
    
    total_imported = fields.Integer('Amount Process', readonly=True)
    notes_process = fields.Text('Notes of Process', readonly=True)
    
    state = fields.Selection([('draft','Start'),('done','Done')], default='draft')
    
    
    def action_process(self):
        for record in self:
            # msg = []
            # if self.sync_type == 'date':
            if self.license_type:
                lictypes = self.env['license.types.management.spt'].SyncFromTTRx(record.connector_id)
            if self.partners:
                partners = self.env['res.partner'].SyncFromTTRx(record.connector_id)
                record.total_imported = len(partners)
            record.state = 'done'
            record.notes_process = "Successfully processed"
        return {  # Recarrega a view após a importação para mostrar resultados
                "type": "ir.actions.act_window",
                "res_model": "sync.partner.spt.wizard",
                "views": [[False, "form"]],
                "name": "Sync Trading Partner",
                "target": "new",
                "res_id": self.id,
        }
            
            
            