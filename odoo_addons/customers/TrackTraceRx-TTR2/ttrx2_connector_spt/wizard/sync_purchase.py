import json
import logging
import urllib.error
import urllib.request as urllib2
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

READ_STATE={'draft': [('readonly', False)]}


class SyncPurchaseSptWizard(models.TransientModel):
    _name = 'sync.purchase.spt.wizard'
    _description = 'Purchase Sync Wizard'
    
    connector_id = fields.Many2one('connector.spt', 'Connector', required=True, readonly=True)
    
    sync_type = fields.Selection([('send','Send'),('receive','Receive'),('both','Send & Receive')], string='Sync', 
                                 required=True, default='receive', readonly=True, states=READ_STATE)
    from_type = fields.Selection([('all','All'), ('single', 'Single'), ('date','a Date')], string='Since', required=True, default='all', readonly=True, 
                                 states=READ_STATE)
    from_date = fields.Date(string='From', default=fields.Date.context_today, readonly=True, states=READ_STATE)
    
    new_only = fields.Boolean(string="New Only", default=False)

    purchase_id = fields.Many2one('purchase.order', string='Purchase', 
                                  domain=[('uuid','!=',False),('state','=','purchase')],readonly=True, states=READ_STATE)

    # Include
    
    total_imported = fields.Integer('Amount Process', readonly=True)
    notes_process = fields.Text('Notes of Process', readonly=True)
    
    state = fields.Selection([('draft','Start'),('done','Done')], default='draft')
    
    
    def action_process(self):
        for record in self:
            pos = self.env['purchase.order']
            if record.from_type == 'single':
                if bool(record.purchase_id) and bool(record.purchase_id.uuid):
                    pos += record.purchase_id.SyncFromTTRx(record.connector_id,MySelf=True)
                else:
                    raise UserError('Enter a valid PO!')
            else:
                for conector in self.env['connector.spt'].search([('state','=','done')]):
                    orders = pos.SyncFromTTRx(connector=conector, NewOnly=True)

                    pos += conector.auto_impexp_purchase(NewOnly=self.new_only)
            record.total_imported = len(pos)
            record.state = 'done'
            record.notes_process = "Successfully processed"
        return {  # Recarrega a view após a importação para mostrar resultados
                "type": "ir.actions.act_window",
                "res_model": "sync.purchase.spt.wizard",
                "views": [[False, "form"]],
                "name": "Sync Purchases",
                "target": "new",
                "res_id": self.id,
        }
            
            
            