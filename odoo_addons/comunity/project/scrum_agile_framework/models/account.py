from odoo import models, fields, api
from datetime import timedelta

class AccountAnalytic(models.Model):
    _inherit = 'account.analytic.line'

    remaining_amount = fields.Float(string='Remaining hours')

    # RELATIONAL MODELS
    sprint_id = fields.Many2one('scrum_agile_framework.sprint', string='Sprint', compute='_get_sprint_id', store=True,
                                ondelete='cascade')
    burn_down_chart_ids = fields.One2many('scrum_agile_framework.burn_down_chart', 'timesheet_id',
                                          string='Burndown chart values')

    # METHODS
    @api.constrains('date')
    def _date_unique(self):
        if self.sprint_id:
            date_counts = self.search_count([('date', '=', self.date), ('id', '!=', self.id),
                                             ('task_id.id', '=', self.task_id.id)])
            if date_counts > 0:
                raise models.ValidationError('The date must be unique,'
                                             'if you want to add an input on this timesheet, modify the existing value.'
                                             )

    @api.depends('task_id.sprint_id')
    def _get_sprint_id(self):
        for line in self:
            if line.task_id.sprint_id:
                line.sprint_id = line.task_id.sprint_id

