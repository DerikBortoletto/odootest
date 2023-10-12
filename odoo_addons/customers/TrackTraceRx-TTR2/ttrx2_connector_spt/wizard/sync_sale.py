import json
import logging
import urllib.error
import urllib.request as urllib2
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

READ_STATE={'draft': [('readonly', False)]}


class SyncSaleSptWizard(models.TransientModel):
    _name = 'sync.sale.spt.wizard'
    _description = 'Sales Sync Wizard'
    
    connector_id = fields.Many2one('connector.spt', 'Connector', required=True, readonly=True)
    
    sync_type = fields.Selection([('send','Send'),('receive','Receive'),('both','Send & Receive')], string='Sync', 
                                 required=True, default='receive', readonly=True, states=READ_STATE)
    from_type = fields.Selection([('all','All'), ('single', 'Single'), ('date','a Date')], string='Since', required=True, default='all', readonly=True, 
                                 states=READ_STATE)
    from_date = fields.Date(string='From', default=fields.Date.context_today, readonly=True, states=READ_STATE)

    new_only = fields.Boolean(string="New Only", default=False)

    sale_id = fields.Many2one('sale.order', string='Sale', domain=[('uuid','!=',False),('state','=','sale')],
                              readonly=True, states=READ_STATE)

    # Include
    
    total_imported = fields.Integer('Amount Process', readonly=True)
    notes_process = fields.Text('Notes of Process', readonly=True)
    
    state = fields.Selection([('draft','Start'),('done','Done')], default='draft')
    
    
    def action_process(self):
        for record in self:
            pos = self.env['sale.order']
            if record.from_type == 'single':
                if bool(record.sale_id) and bool(record.sale_id.uuid):
                    pos += record.sale_id.SyncFromTTRx(record.connector_id,MySelf=True)
                else:
                    raise UserError('Enter a valid SO!')
            else:    
                for conector in self.env['connector.spt'].search([('state','=','done')]):
                    pos += conector.auto_impexp_sale(NewOnly=self.new_only)
            record.total_imported = len(pos)
            record.state = 'done'
            record.notes_process = "Successfully processed"
        return {  # Recarrega a view após a importação para mostrar resultados
                "type": "ir.actions.act_window",
                "res_model": "sync.sale.spt.wizard",
                "views": [[False, "form"]],
                "name": "Sync Sales",
                "target": "new",
                "res_id": self.id,
        }
            
            
            