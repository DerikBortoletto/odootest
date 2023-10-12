
from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    format_lot = fields.Char('Lot/Serial Format', default="%s%s")
    lot_sequence_id = fields.Many2one("ir.sequence", string="Lot sequence", ondelete="restrict")
    serial_sequence_id = fields.Many2one("ir.sequence", string="Serial sequence", ondelete="restrict")
    
    
    
