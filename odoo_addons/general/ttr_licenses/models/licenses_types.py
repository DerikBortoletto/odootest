# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class LicencesTypes(models.Model):
    _name = 'licenses.types'
    _description = "Licenses Types"

    name = fields.Char(string='License Name', required=True)
    code = fields.Char(string='License Code', required=True)
    observation = fields.Text(string='Obs:')
