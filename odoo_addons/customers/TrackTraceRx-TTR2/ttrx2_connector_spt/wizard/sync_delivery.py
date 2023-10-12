import json
import logging
import urllib.error
import urllib.request as urllib2
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

READ_STATE={'draft': [('readonly', False)]}


class SyncDeliverySptWizard(models.TransientModel):
    _name = 'sync.delivery.spt.wizard'
    _description = 'Delivery Sync Wizard'
    
    connector_id = fields.Many2one('connector.spt', 'Connector', required=True, readonly=True)
    
    sync_type = fields.Selection([('send','Send'),('receive','Receive'),('both','Send & Receive')], string='Sync', 
                                 required=True, default='receive', readonly=True, states=READ_STATE)
    from_type = fields.Selection([('all','All'), ('single', 'Single'), ('date','a Date')], string='Since', required=True, default='all', readonly=True, 
                                 states=READ_STATE)
    from_date = fields.Date(string='From', default=fields.Date.context_today, readonly=True, states=READ_STATE)

    transfer_id = fields.Many2one('stock.picking', string='Transfer', domain=[('uuid','!=',False),('state','!=','done'),('picking_type_code','=','outgoing')],
                                  readonly=True, states=READ_STATE)

    # Include
    
    total_imported = fields.Integer('Amount Process', readonly=True)
    notes_process = fields.Text('Notes of Process', readonly=True)
    
    state = fields.Selection([('draft','Start'),('done','Done')], default='draft')
    
    
    def action_process(self):
        for record in self:
            total = 0
            if record.from_type == 'single':
                if bool(record.transfer_id) and bool(record.transfer_id.uuid):
                    primary_model = record.transfer_id.picking_type_id.code
                    record.transfer_id.SyncFromTTRx(record.transfer_id.connector_id,primary_model=primary_model,MySelf=True)
                    total = 1
                else:
                    raise UserError('Enter a valid Transfer Delivery!')
            else:    
                regs = self.env['connector.spt']._cron_get_transfers_out()
                total = len(regs)
            record.total_imported = total
            record.state = 'done'
            record.notes_process = "Successfully processed"
        return {  # Recarrega a view após a importação para mostrar resultados
                "type": "ir.actions.act_window",
                "res_model": "sync.delivery.spt.wizard",
                "views": [[False, "form"]],
                "name": "Delivery Sync Wizard",
                "target": "new",
                "res_id": self.id,
        }
            
            
            