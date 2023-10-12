from odoo import models, fields, api
from datetime import timedelta

class Sprint(models.Model):
    _name = 'scrum_agile_framework.sprint'
    _description = 'Allows defining the sprints assigned to a project'
    _order = 'date_start'

    name = fields.Char(string='Sprint', required=True)
    date_start = fields.Date('Start date', required=True, default=fields.date.today())
    date_end = fields.Date(string='End date', required=True)
    speed = fields.Integer(string='Speed')
    goal = fields.Char(string='Goal')
    conclusions = fields.Text(string='Conclusions')
    task_count = fields.Integer(compute='_compute_task_count')
    retro_well = fields.Text(string='What went well?')
    retro_improvement = fields.Text(string='What went wrong?')
    retro_improvement_action = fields.Text(string="What should we do differently next time?")
    total_estimated_hours = fields.Integer(string='Total estimated hours', compute='_get_estimated_hours',
                                           store=True)

    # RELATIONAL MODELS
    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    user_story_ids = fields.One2many('scrum_agile_framework.user_story', 'sprint_id', string='User stories')
    task_ids = fields.One2many('project.task', 'sprint_id', string='Tasks')
    account_analytic_ids = fields.One2many('account.analytic.line', 'sprint_id', string='Timesheet')
    burn_down_chart_ids = fields.One2many('scrum_agile_framework.burn_down_chart', 'sprint_id', string='Burndown charts')

    # METHODS
    def action_view_tasks_scrum(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('scrum_agile_framework.action_sprint_kanban_tasks') \
            .sudo().read()[0]
        action['display_name'] = self.name
        return action

    def action_view_burn_scrum(self):
        for burn_down_chart in self.burn_down_chart_ids:
            if not burn_down_chart.timesheet_id:
                burn_down_chart.unlink()
        for sprint in self:
            sprint.sudo()._create_burndown_chart_values()
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('scrum_agile_framework.action_sprint_burn') \
            .sudo().read()[0]
        action['display_name'] = self.name
        return action

    @api.depends('user_story_ids.planned_hours')
    def _get_estimated_hours(self):
        for sprint in self:
            sprint.total_estimated_hours = sum(user_story.planned_hours for user_story in sprint.user_story_ids)

    def _create_burndown_chart_values(self):
        self.ensure_one()
        vals_list = []
        work_hours_data = self._get_time_day(
            self.date_start,
            self.date_end,
        )
        for task in self.task_ids:
            if task.scrum_stage == 'todo':
                for index, (day_date, hours_day) in enumerate(work_hours_data):
                    vals_list.append(
                        self._timesheet_task_prepare_line_values(day_date, task.planned_hours))
            else:
                for timesheet in task.timesheet_ids:
                    vals_list.append(
                        self._timesheet_task_prepare_line_values(timesheet.date, timesheet.remaining_amount))

        for index, (day_date, hours_day) in enumerate(work_hours_data):
            vals_list.append(self._timesheet_prepare_line_values(day_date, hours_day))
        self.env['scrum_agile_framework.burn_down_chart'].sudo().create(vals_list)

    def _timesheet_task_prepare_line_values(self, day_date, remaining_amount):
        self.ensure_one()
        return {
            'name': 'Remaining effort',
            'date': day_date,
            'hours_day': remaining_amount,
            'sprint_id': self.id,
        }

    def _timesheet_prepare_line_values(self, day_date, hours_day):
        self.ensure_one()
        return {
            'name': 'Expected effort',
            'date': day_date,
            'hours_day': hours_day,
            'sprint_id': self.id,
        }

    def _get_time_day(self, from_datetime, to_datetime):
        hours_sum = self.total_estimated_hours
        total_days = (to_datetime - from_datetime).days
        hours_day = round((hours_sum / total_days), 4)
        work_day_list = []
        for dt in self.daterange(from_datetime, to_datetime):
            work_day_list.append((dt, hours_sum))
            hours_sum = (hours_sum - hours_day)
        return work_day_list

    @staticmethod
    def daterange(date1, date2):
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + timedelta(n)

    @api.model_create_multi
    def create(self, vals_list):
        sprints = super(Sprint, self).create(vals_list)
        for sprint in sprints:
            sprint.sudo()._create_burndown_chart_values()
        return sprints


