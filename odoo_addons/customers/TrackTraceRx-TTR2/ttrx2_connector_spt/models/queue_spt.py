import logging

from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo, StrToFloat

_logger = logging.getLogger(__name__)

class queue_spt(models.Model):
    _name = 'queue.spt'
    _inherit = "custom.connector.spt"
    _description = 'List of Queues'
    _order = 'created_on, uuid'
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'uuid': 'uuid'}
    _TTRxToOdoo = {'uuid': 'uuid'}


    # TTRx Fields
    uuid = fields.Char("UUID Queue", copy=False, readonly=True)
    created_on = fields.Datetime('Create On', readonly=True)
    name = fields.Char('Task Name', readonly=True)
    estimated_duration = fields.Datetime('Estimated Duration', readonly=True)
    status = fields.Char('Status', readonly=True)
    eta_datetime = fields.Datetime('Eta Date/Time', readonly=True)
    eta_seconds = fields.Integer('Eta Seconds', readonly=True)
    result = fields.Char('Result', readonly=True)
    res_model_id = fields.Many2one('ir.model', string='Model')
    res_model_name = fields.Char(related='res_model_id.model', string='Model Name', readonly=True, store=True)
    res_id = fields.Integer('ID Reg')
    res_uuid = fields.Char('Status')

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, '[%s] %s' % (record.uuid, record.name or '')))
        return res
    
    # Funções De/Para    

    def FromTTRxToOdoo(self, connector, values):
        var = super().FromTTRxToOdoo(connector=connector,values=values)
        var.update({
            'uuid': values['uuid'],
            'created_on': DateTimeToOdoo(values.get('created_on', None)),
            'name': values.get('task_name',None),
            'estimated_duration': DateTimeToOdoo(values.get('estimated_duration', None)),
            'status': values.get('status',None),
            'eta_datetime': DateTimeToOdoo(values.get('eta_datetime', None)),
            'eta_seconds': values.get('eta_seconds',None),
            'result': values.get('result',None),
            'res_model_id': values.get('res_model_id',None),
            'res_id': values.get('res_id',None),
            'res_uuid': values.get('res_uuid',None),
        })
        CleanDataDict(var)
        return var

