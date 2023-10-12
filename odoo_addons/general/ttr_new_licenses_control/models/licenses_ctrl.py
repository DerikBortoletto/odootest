#  -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.fields import Many2one


class Licences(models.Model):
    _name = 'licenses.ctrl'
    _description = "New Licenses Control"


    licenses_list = fields.Many2one('license.spt', 'licenses')
    responsible_ids = fields.Many2one('res.users', string='Responsible')
    type_ids = fields.Many2one('license.types.management.spt', string='Licenses Type')
    tt_id = fields.Char(related='licenses_list.tt_id', string='TTRx2 ID')
    valid_from = fields.Date(related='licenses_list.valid_from', required=True, string='Validity Start')
    valid_to = fields.Date(related='licenses_list.valid_to', string='Expiration Date', required=True)
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
