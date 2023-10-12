import re
import base64
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.l10n_br_op_base.tools.fiscal import IND_IE_DEST

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    indicador_ie_dest = fields.Selection(IND_IE_DEST, string="Indicador IE", 
                                         help="Caso não preencher este campo vai usar a \
                                               regra:\n9 - para pessoa física\n1 - para pessoa jurídica com IE \
                                               cadastrada\n2 - para pessoa jurídica sem IE cadastrada ou 9 \
                                               caso o estado de destino for AM, BA, CE, GO, MG, MS, MT, PE, RN, SP")

    @api.onchange('inscr_est','company_type')
    def onchange_inscr_est(self):
        if self.company_type == "company":
            if bool(self.inscr_est):
                self.indicador_ie_dest = "1"
            elif self.state_id.code in ['AM','BA','CE','GO','MG','MS','MT','PE','RN','SP']:
                self.indicador_ie_dest = "9"
            else:
                self.indicador_ie_dest = "2"
        else:
            self.indicador_ie_dest = "9"
