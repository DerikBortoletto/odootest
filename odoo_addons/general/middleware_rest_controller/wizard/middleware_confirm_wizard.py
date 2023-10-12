# -*- coding: utf-8 -*-
from odoo import models, fields

class MiddlewareConfirmWizard(models.TransientModel):
    _name = "middleware.confirm.wizard"
    _description = "Middleware Confirm Wizard"
    message = fields.Text("message")

    def however_continue(self):
        order = self.env.context.get("order", None)
        if order == "purchase":
            po_id = self.env.context.get("id")
            po = self.env["purchase.order"].sudo().search([("id", "=", int(po_id))])
            if bool(po):
                ctx = self.env.context.copy()
                ctx.update({"is_not_confirmed": False})
                return po.with_context(ctx).button_confirm()
        elif order == "sale":
            so_id = self.env.context.get("id")
            so = self.env["sale.order"].sudo().search([("id", "=", int(so_id))])
            if bool(so):
                ctx = self.env.context.copy()
                ctx.update({"is_not_confirmed": False})
                return so.with_context(ctx).action_confirm()
