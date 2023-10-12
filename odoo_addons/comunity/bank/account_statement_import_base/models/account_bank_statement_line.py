
from odoo import fields, models

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    # Ensure transactions can be imported only once
    # if the import format provides unique transaction IDs
    unique_import_id = fields.Char(string="Import ID", readonly=True, copy=False)
    raw_data = fields.Text(readonly=True, copy=False)

    _sql_constraints = [("unique_import_id", "unique(unique_import_id)", 
                         "A bank account transaction can be imported only once!")]
