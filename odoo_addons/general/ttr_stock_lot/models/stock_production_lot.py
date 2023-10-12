
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.production.lot'
    _order = 'company_id,product_id,display_name'

    name = fields.Char('Lot Number', default=False, required=True, help="Lot Number representation", index=True)
    serial = fields.Char('Serial Number', default=False, help="Unique Serial Number Representation", index=True)
    format_field = fields.Char('Lot/Serial Format')
    display_name = fields.Char('Lot/Serial Name', compute='_compute_display_name', store=True, index=True, readonly=True)
    tracking = fields.Selection(related='product_id.tracking')

    _sql_constraints = []

    @api.constrains('display_name', 'serial', 'product_id', 'company_id')
    def _check_unique_lot(self):
        ids = self.product_id.filtered(lambda x: x.tracking == "lot").ids
        if bool(ids):
            domain = [('product_id', 'in', ids),
                      ('company_id', 'in', self.company_id.ids),
                      ('name', 'in', self.mapped('name')),
                      ('serial', '=', self.serial)]
            fields = ['company_id', 'product_id', 'name']
            groupby = ['company_id', 'product_id', 'name']
            records = self.read_group(domain, fields, groupby, lazy=False)
            error_message_lines = []
            for rec in records:
                if rec['__count'] != 1:
                    product_name = self.env['product.product'].browse(rec['product_id'][0]).display_name
                    error_message_lines.append(" - Product: %s, Lot Number: %s" % (product_name, rec['name']))
            if error_message_lines:
                raise ValidationError('The combination of lot number and product must be unique across a company.\nFollowing combination contains duplicates:\n' + '\n'.join(error_message_lines))

        ids = self.product_id.filtered(lambda x: x.tracking == "serial").ids
        if bool(ids):
            domain = [('product_id', 'in', ids),
                      ('company_id', 'in', self.company_id.ids),
                      ('name', 'in', self.mapped('name')),
                      ('serial', 'in', self.mapped('serial')),]
            fields = ['company_id', 'product_id', 'name', 'serial']
            groupby = ['company_id', 'product_id', 'name', 'serial']
            records = self.read_group(domain, fields, groupby, lazy=False)
            error_message_lines = []
            for rec in records:
                if rec['__count'] != 1:
                    product_name = self.env['product.product'].browse(rec['product_id'][0]).display_name
                    error_message_lines.append(" - Product: %s, Serial Number: %s", product_name, rec['name'])
            if error_message_lines:
                raise ValidationError('The combination of serial number and product must be unique across a company.\nFollowing combination contains duplicates:\n') + '\n'.join(error_message_lines)
    

    @api.depends('name', 'serial', 'format_field')
    def _compute_display_name(self):
        for reg in self:
            if reg.tracking == 'serial':
                format_vl = reg.format_field or '%s%s'  
                reg.display_name = format_vl % (reg.name, reg.serial or '')
            else:
                reg.display_name = reg.name


    @api.onchange('product_id')
    def _onchange_product_id(self):
        for reg in self:
            reg.format_field = self.product_id.format_lot

    @api.model
    def create(self, values):
        created = super(StockLocation, self).create(values)
        return created
            