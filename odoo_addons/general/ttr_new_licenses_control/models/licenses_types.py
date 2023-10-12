from odoo import models, fields


class LicencesTypes(models.Model):
    _name = 'licenses.types'
    _description = "Licenses Types"

    type_list = fields.Many2one('license.types.management.spt', string='Responsible')
    name = fields.Char(related='type_list.name', string='License Name', required=True)
    code = fields.Char(related='type_list.code', string='License Code', required=True)
    observation = fields.Text(string='Obs:')