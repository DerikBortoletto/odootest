from odoo import models, fields, api
from datetime import timedelta

class Team(models.Model):
    _name = 'scrum_agile_framework.team'
    _description = 'Allows defining the members of the Scrum Team'

    name = fields.Char(string='Scrum Team name', required=True)

    # RELATIONAL MODELS
    project_ids = fields.One2many('project.project', 'team_id', string='Project')
    meeting_ids = fields.One2many('scrum_agile_framework.meeting', 'team_id', string='Meeting')
    employee_ids = fields.Many2many('hr.employee', string='Employee')


