
from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_id = fields.Many2one('product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 change_default=True, ondelete='restrict', check_company=True)
    pharm_description = fields.Char(string="Product Description", related="product_id.pharm_description", store=False, readonly=True)
    generic_name = fields.Char(string="Generic Name", related="product_id.generic_name", store=False, readonly=True)
    manufacture_id = fields.Many2one('res.partner', string='Manufacture', related="product_id.manufacture_id", store=False, readonly=True)
    item_class = fields.Selection(string="Class", related="product_id.item_class", store=False, readonly=True)
    control_substance = fields.Boolean(string='Control Substance', related="product_id.control_substance", store=False, readonly=True)
    control_substance_type = fields.Selection(string="Control Type", related="product_id.control_substance_type", store=False, readonly=True)
    storage_temperature = fields.Selection(string="Temperature", related="product_id.storage_temperature", store=False, readonly=True)
    size = fields.Selection(string="Size", related="product_id.size", store=False, readonly=True)
