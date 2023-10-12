from odoo import fields, models





class ResState(models.Model):
    _inherit = 'res.country.state'
    
    ttr_state_id = fields.Integer('TTR State Id')
    connector_id = fields.Many2one('connector.spt', 'Connector')
