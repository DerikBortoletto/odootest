import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)




class tracktrace_log_spt(models.Model):
    _name = 'tracktrace.log.spt'
    _description = 'Log for api call'
    _order = "create_date desc"
    
    type = fields.Selection([('info','Information'),('warn','Warning'),('error','Error')],string='Type of Log', default='info')
    create_date = fields.Datetime('Create On', default=fields.Datetime.now)
    method = fields.Char('Method', required=True, default="GET")
    model = fields.Char('Model')
    res_id = fields.Integer('Id Model')
    message = fields.Text("Message", required=True)
    connector_id = fields.Many2one('connector.spt', 'Connector')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, 
                                 default=lambda self: self.env.user.company_id)
    group_id = fields.Char('# Group')

    @api.model
    def addLog(self, connector_id, method, model, message, typein="info", model_id=0, group_id=False):
        val = {
            'connector_id': connector_id,
            'method': method,
            'message': message,
            'model': model,
            'res_id': model_id,
            'type': typein,
            'create_date': fields.Datetime.now(),
            'group_id': group_id,
        }
        return self.create(val)

    @api.model
    def create(self, values):
        if values.get('type', 'info') == 'warn':
            _logger.debug('### Informe TTRx2 comunication %s, %s, %s (%s)' % (
                                                                 values.get('code', '00000'),
                                                                 values.get('method', '[unknow]'),
                                                                 values.get('model', '[unknow]'),
                                                                 values.get('message','[unknow]')))
        elif values.get('type', 'warn') == 'error':
            _logger.info('### Warning TTRx2 comunication %s, %s, %s, (%s)' % (
                                                                 values.get('code', '00000'),
                                                                 values.get('method', ''),
                                                                 values.get('model', '[unknow]'),
                                                                 values.get('message','')))
        elif values.get('type', 'error') == 'error':
            _logger.error('### Error TTRx2 comunication %s, %s, %s, (%s)' % (
                                                                 values.get('code', '00000'),
                                                                 values.get('method', ''),
                                                                 values.get('model', '[unknow]'),
                                                                 values.get('message','')))
        return super(tracktrace_log_spt, self).create(values)

