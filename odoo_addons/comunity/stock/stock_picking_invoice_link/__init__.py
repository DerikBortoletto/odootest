# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from . import models

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    pickings = env['stock.picking'].search([('picking_type_code', 'in', ['incoming','outgoing']),('state','=','done')])
    _logger.info('Start the invoice link in picking')
    for picking in pickings:
        invoice_ids = set()
        for move in picking.move_lines:
            if bool(move.sale_line_id):
                for invoice_line in move.sale_line_id.invoice_lines:
                    invoice_ids.add(invoice_line.move_id.id)
            if bool(move.purchase_line_id):
                for invoice_line in move.purchase_line_id.invoice_lines:
                    invoice_ids.add(invoice_line.move_id.id)
        picking.invoice_ids = [(6, 0, (list(invoice_ids)))]
    _logger.info('Ended the invoice link in picking')
        