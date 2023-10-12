from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class TradeBills(models.Model):
    _name = "account.maturities"
    _description = "Maturity Entries"
    _order = "date_due, id"

    @api.model
    def _get_default_currency(self):
        ''' Get the default currency from either the journal, either the default journal's company. '''
        return self.company_id.currency_id or self.env.company

    move_id = fields.Many2one('account.move', string='Journal Entry', index=True, required=True, 
                              readonly=True, auto_join=True, ondelete="cascade", 
                              help="The move of this entry line.")
    move_name = fields.Char(string='Number', related='move_id.name', store=True, index=True)
    date = fields.Date(related='move_id.date', store=True, readonly=True, index=True, copy=False)
    company_id = fields.Many2one(related='move_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
                                  string='Currency', default=_get_default_currency)
    date_due = fields.Date(required=True, string="Due date")
    value = fields.Float(required=True, copy=False, string="Value")

