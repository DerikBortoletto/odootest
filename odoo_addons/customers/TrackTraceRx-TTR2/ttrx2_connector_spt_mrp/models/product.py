from odoo import models, fields, api
from odoo.exceptions import UserError

class product_template(models.Model):
    _inherit = 'product.template'
    

class product_product(models.Model):
    _inherit = 'product.product'
    
    tracktrace_is = fields.Boolean('Is TrackTraceRx2',compute="_compute_tracktrace", store=False)
    product_spt_id = fields.Many2one('product.spt',string='Product SPT',compute="_compute_tracktrace", store=False)
    
    def _compute_tracktrace(self):
        for reg in self:
            reg.product_spt_id = self.env['product.spt'].search([('product_id','=',self.id)],limit=1)
            reg.tracktrace_is = bool(reg.product_spt_id)

        