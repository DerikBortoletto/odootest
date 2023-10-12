# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    ticket_id = fields.Many2one('helpdesk.ticket', 'Ticket', index=True, ondelete='set null')

    def _compute_is_highlighted(self):
        super(CalendarEvent, self)._compute_is_highlighted()
        if self.env.context.get('active_model') == 'helpdesk.ticket':
            ticket_id = self.env.context.get('active_id')
            for event in self:
                if event.ticket_id.id == ticket_id:
                    event.is_highlighted = True

    @api.model_create_multi
    def create(self, vals):
        events = super(CalendarEvent, self).create(vals)
        # for event in events:
        #     if event.ticket_id and not event.activity_ids:
        #         event.ticket_id.log_meeting(event.name, event.start, event.duration)
        return events

