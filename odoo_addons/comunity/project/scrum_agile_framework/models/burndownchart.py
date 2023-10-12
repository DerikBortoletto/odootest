from odoo import models, fields, api
from datetime import timedelta


class BurnDownChart(models.Model):
    _name = 'scrum_agile_framework.burn_down_chart'
    _description = 'This class gets all the data from the timesheet to create the Burndown chart graph'

    name = fields.Char(string='Allows to distinguish between Remaining effort and Anticipated effort ')
    date = fields.Date(string='Date', required=True)
    hours_day = fields.Float(string='The number of hours per day', required=True)

    # RELATIONAL MODELS
    sprint_id = fields.Many2one('scrum_agile_framework.sprint', string='Sprint', ondelete='cascade')
    timesheet_id = fields.Many2one('account.analytic.line', string='Timesheet', ondelete='cascade')


