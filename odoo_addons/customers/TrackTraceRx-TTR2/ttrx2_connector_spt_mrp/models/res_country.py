from odoo import fields, models





class ResCountry(models.Model):
    _inherit = 'res.country'
    
    ttr_country_id = fields.Integer('TTR Country Id')
    connector_id = fields.Many2one('connector.spt', 'Connector')
