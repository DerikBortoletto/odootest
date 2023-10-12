# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class Licences(models.Model):
    _name = 'licenses.control'
    _description = "Licenses Control"

    responsible_ids = fields.Many2one('res.users', string='Responsible')
    type_ids = fields.Many2one('licenses.types', string='License Type')
    name = fields.Char(string='Name/Description', required=True, translate=True)
    validity_start = fields.Date(string='Validity Start')
    expiration_date = fields.Date(string='Expiration Date')
    renewal_date = fields.Date(string='Renewal Date')
    license_state = fields.Selection([('draft', 'Draft'), ('in_use', 'In_Use'), ('done', 'Done')
                                      ], required=True, translate=True,)
    observation = fields.Text(string='Obs:')
    attachment_id = fields.Many2many('ir.attachment', widget="many2many_binary", string=" License Attachment")


    def action_renewal_date(self):
        participants = [self.responsible_ids]
        event = {
            'name': 'Alarm of Renewal date ' % self.name,
            'alarm_type': 'notification',
            'duration': 360,
        }
        data = {
            'name': 'Reminder: %s' % self.name,
            'start': self.date,
            'allday': True,
            'location': 'Calendar user' % self.id,
            'user_id': self.current_user.id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)], limit=1).id,
            'partner_ids': [(6, False, participants)],
            'alarm_ids': [(0, 0, event)],
        }
        self.env['calendar.event'].create(data)

