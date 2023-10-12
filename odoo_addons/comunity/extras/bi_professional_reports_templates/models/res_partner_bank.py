from odoo import fields, models

class res_partner_bank(models.Model):
    _inherit = "res.partner.bank"

    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', size=24, change_default=True)
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", 'State')
    country_id = fields.Many2one('res.country', 'Country')
    swift_code = fields.Char('Swift Code')
    ifsc = fields.Char('IFSC')
    branch_name = fields.Char('Branch Name')