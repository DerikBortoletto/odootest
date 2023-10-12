# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class medical_physician(models.Model):
    _name="medical.physician"
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner','Physician',required=True)
    institution_partner_id = fields.Many2one('res.partner',domain=[('is_institution','=',True)],string='Institution')
    code = fields.Char('CRM')
    medical_specialty= fields.Char('Medical Specialty')
    info = fields.Text('Extra Info')

    name = fields.Char(related='partner_id.name', readonly=True)
    email = fields.Char(related='partner_id.email', readonly=True)
    phone = fields.Char(related='partner_id.phone', readonly=True)

    institution = fields.Char(related='partner_id.street', readonly=True)
    city = fields.Char(related='partner_id.city', readonly=True)
    state = fields.Many2one(related='partner_id.state_id', readonly=True)
    country_code = fields.Many2one(related='partner_id.country_id', readonly=True)


