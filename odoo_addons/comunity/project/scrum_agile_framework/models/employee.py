from odoo import models, fields, api
from datetime import timedelta

class Employee(models.Model):
    _inherit = 'hr.employee'
    _order = 'role'

    role = fields.Selection(string='role', selection=[(
        'po', 'Product Owner'), ('sm', 'Scrum Manager'), ('dt', 'Development Team')], default='dt')

    responsibility = fields.Char(string='Responsibility')

    # RELATIONAL MODELS
    team_ids = fields.Many2many('scrum_agile_framework.team', string='Team')


