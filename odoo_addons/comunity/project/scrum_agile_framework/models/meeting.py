from odoo import models, fields, api
from datetime import timedelta

class Meeting(models.Model):
    _name = 'scrum_agile_framework.meeting'
    _description = 'Allows defining routine meetings of the Scrum Team'
    _order = 'date'

    date = fields.Datetime(string='Date', required=True)
    date_delay = fields.Float(string='Duration', compute='_get_duration_float', store=True)
    type = fields.Selection(string='Type', selection=[('plan', 'Sprint Planning'), 
                                                      ('review', 'Sprint Review'), 
                                                      ('retrospective', 'Sprint Retrospective'), 
                                                      ('daily', 'Daily Scrum')], default='daily')
    duration = fields.Char('Duration', compute='_get_duration', store=True, help='Maximum meeting duration')

    # RELATIONAL MODELS
    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    team_id = fields.Many2one('scrum_agile_framework.team', string='Team', ondelete='cascade', compute='_get_team')

    # METHODS
    @api.depends('type')
    def _get_duration_float(self):
        for meeting in self:
            if meeting.type == 'daily':
                meeting.date_delay = 0.25
            elif meeting.type == 'review':
                meeting.date_delay = 2.0
            elif meeting.type == 'retrospective':
                meeting.date_delay = 1.5
            elif meeting.type == 'plan':
                meeting.date_delay = 4.0

    @api.depends('type')
    def _get_duration(self):
        meeting_duration = {'daily': '15 minutes', 'review': '2 hours',
                            'retrospective': '1 hour and a half', 'plan': '4 hours'}
        for meeting in self:
            meeting.duration = meeting_duration[f'{meeting.type}']

    @api.depends('project_id')
    def _get_team(self):
        for meeting in self:
            meeting.team_id = meeting.project_id.team_id

    def name_get(self):  # odoo's own function
        result = []
        for meeting in self:
            description = dict(meeting._fields['type'].selection).get(meeting.type) +\
                          f' Meeting of the Project: {meeting.project_id.name} '
            result.append((meeting.id, description))
        return result


