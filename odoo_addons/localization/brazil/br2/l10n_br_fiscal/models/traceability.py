# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _

class Traceability(models.Model):
    _name = "l10n_br_fiscal.traceability"
    # _inherit = ["nfe.40.rastro"]
    _description = "Traceability"
    
    sequence = fields.Integer(string="Sequência", default=10)
    document_line_id = fields.Many2one('l10n_br_fiscal.document.line', string='Line Document Entry',
                                       index=True, required=True, auto_join=True, ondelete="cascade")
    name = fields.Char('Lot/Serial Number', required=True, help="Unique Lot/Serial Number")
    product_qty = fields.Float('Quantity')
    expiration_date = fields.Date(string='Expiration Date')
    manufacture_date = fields.Date(string='Manufacture Date')
    
    
    @api.model
    def create(self, vals):
        return super(Traceability, self).create(vals)
    
    def write(self, vals):
        res = super(Traceability, self).write(vals)
        return res