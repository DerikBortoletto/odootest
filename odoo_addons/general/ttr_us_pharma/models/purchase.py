
from odoo import models, fields, api
from odoo.exceptions import UserError

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True)
    pharm_description = fields.Char(string="Product Description", related="product_id.pharm_description", store=False, readonly=True)
    generic_name = fields.Char(string="Generic Name", related="product_id.generic_name", store=False, readonly=True)
    manufacture_id = fields.Many2one('res.partner', string='Manufacture', related="product_id.manufacture_id", store=False, readonly=True)
    item_class = fields.Selection(string="Class", related="product_id.item_class", store=False, readonly=True)
    control_substance = fields.Boolean(string='Control Substance', related="product_id.control_substance", store=False, readonly=True)
    control_substance_type = fields.Selection(string="Control Type", related="product_id.control_substance_type", store=False, readonly=True)
    storage_temperature = fields.Selection(string="Temperature", related="product_id.storage_temperature", store=False, readonly=True)
    size = fields.Selection(string="Size", related="product_id.size", store=False, readonly=True)

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        super(PurchaseOrderLine, self)._get_product_purchase_description(product_lang)
        name = product_lang.name
        if product_lang.pharm_description:
            if product_lang.generic_name:
                name = product_lang.pharm_description
            else:
                name += ' ' + product_lang.pharm_description
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        return name
