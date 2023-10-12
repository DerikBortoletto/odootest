import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)




class tracktrace_log_spt(models.Model):
    _name = 'tracktrace.log.spt'
    _description = 'Log for api call'
    _order = "create_date desc"
    
    type = fields.Selection([('info','Information'),('warn','Warning'),('error','Error')],string='Type of Log', default='info')
    create_date = fields.Datetime('Created On', default=fields.Datetime.now)
    method = fields.Char('Method', required=True, default="GET")
    model = fields.Char('Model')
    message = fields.Char("Message", required=True)

    connector_id = fields.Many2one('connector.spt', 'Connector')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, 
                                 default=lambda self: self.env.user.company_id)

    @api.model
    def addLog(self, connector, method, model, message, typein="info"):
        val = {
            'connector_id': connector,
            'method': method,
            'message': message,
            'model': model,
            'type': typein,
            'create_date': fields.Datetime.now,
        }
        return self.create(val)

    @api.model
    def create(self, values):
        if values.get('type', 'info') == 'info':
            _logger.debug('TTRx2 comunication %s, %s, %s, %s' % (values.get('type', 'info'),
                                                                 values.get('code', '00000'),
                                                                 values.get('method', ''),
                                                                 values.get('message','')))
        else:
            _logger.error('TTRx2 comunication %s, %s, %s, %s' % (values.get('type', 'error'),
                                                                 values.get('code', '00000'),
                                                                 values.get('method', ''),
                                                                 values.get('message','')))
        return super(tracktrace_log_spt, self).create(values)
        
