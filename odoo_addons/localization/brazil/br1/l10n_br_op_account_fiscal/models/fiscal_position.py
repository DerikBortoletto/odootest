from odoo import api, fields, models, _
from odoo.addons.l10n_br_op_account_base.cst import CST_ICMS, CSOSN_SIMPLES, ORIGEM_PROD, CST_IPI, CST_PIS_COFINS

class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

