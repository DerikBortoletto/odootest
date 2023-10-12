# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models





class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'
    
    module_product_expiry = fields.Boolean("Expiration Dates", default=True, help="""Track  following dates on lots & serial numbers: \n\r
                            best before, removal, end of life, alert. \n\r 
                            Such dates are set automatically at lot/serial number \n\r
                            creation based on values set on the product (in days).""")


    wharehouse_ttr = fields.Many2one(related="company_id.wharehouse_ttr", readonly=False)
    
    lot_number = fields.Selection(related="company_id.lot_number", readonly=False)
    
    serial_number = fields.Selection(related="company_id.serial_number", readonly=False)
    
    strict_inventory_policies = fields.Boolean(related="company_id.strict_inventory_policies", readonly=False)
    
    edi_source = fields.Selection(related="company_id.edi_source", readonly=False)
    epcis_source = fields.Selection(related="company_id.epcis_source", readonly=False)
    other_source = fields.Selection(related="company_id.other_source", readonly=False)
    unknown_products = fields.Selection(related="company_id.unknown_products", readonly=False)
    