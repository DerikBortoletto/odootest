# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_ids = fields.Many2many(comodel_name="account.move", copy=False, string="Invoices", readonly=True)

    def action_view_invoice(self):
        """This function returns an action that display existing invoices
        of given stock pickings.
        It can either be a in a list or in a form view, if there is only
        one invoice to show.
        """
        self.ensure_one()
        form_view_name = "account.view_move_form"
        xmlid = "account.action_move_out_invoice_type"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        if len(self.invoice_ids) > 1:
            action["domain"] = "[('id', 'in', %s)]" % self.invoice_ids.ids
        else:
            form_view = self.env.ref(form_view_name)
            action["views"] = [(form_view.id, "form")]
            action["res_id"] = self.invoice_ids.id
        return action

    def action_link_to_invoice(self):
        for picking in self:
            invoice_ids = set()
            for move in picking.move_lines:
                if bool(move.sale_line_id):
                    for invoice_line in move.sale_line_id.invoice_lines:
                        invoice_ids.add(invoice_line.move_id.id)
                if bool(move.purchase_line_id):
                    for invoice_line in move.purchase_line_id.invoice_lines:
                        invoice_ids.add(invoice_line.move_id.id)
            picking.invoice_ids = [(6, 0, (list(invoice_ids)))]
                        
        