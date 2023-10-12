from odoo import models, fields, api
from datetime import timedelta

class UserStory(models.Model):
    _name = 'scrum_agile_framework.user_story'
    _description = 'Allows you to manage the user stories of a project'
    _order = 'sequence , priority desc, id desc'

    name = fields.Char(string='Name', required=True)
    priority = fields.Integer(string='Priority', required=True)
    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of user stories.")
    planned_hours = fields.Float('Planned hours', compute='_compute_planned_hours_sum')
    effective_hours = fields.Float('Effective hours', compute='_compute_effective_hours_sum')
    state = fields.Char('State')
    notes = fields.Char('Notes')
    editable = fields.Boolean('User story editable', compute='_user_story_editable', store=True)

    # RELATIONAL MODELS
    project_id = fields.Many2one('project.project', string='Project', compute='_get_project_id_from_sprint',
                                 store=True, ondelete='cascade')
    sprint_id = fields.Many2one('scrum_agile_framework.sprint', string='Sprint')
    task_ids = fields.One2many('project.task', 'user_story_id', string='Tasks')

    # METHODS
    @api.depends('task_ids.planned_hours')
    def _compute_planned_hours_sum(self):
        for user_story in self:
            user_story.planned_hours = sum(task.planned_hours for task in user_story.task_ids)

    @api.depends('task_ids.timesheet_ids.unit_amount')
    def _compute_effective_hours_sum(self):
        for user_story in self:
            user_story.effective_hours = sum(timesheet.unit_amount for task in user_story.task_ids
                                             for timesheet in task.timesheet_ids)

    @api.depends('sprint_id.project_id')
    def _get_project_id_from_sprint(self):
        for user_story in self:
            if user_story.sprint_id:
                user_story.project_id = user_story.sprint_id.project_id

    def action_view_tasks_hu_scrum(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('scrum_agile_framework.action_hu_kanban_tasks') \
            .sudo().read()[0]
        action['display_name'] = self.name
        return action

    @api.depends('project_id.last_sprint_id')
    def _user_story_editable(self):
        for user_story in self:
            if user_story.sprint_id:
                if user_story.sprint_id == user_story.project_id.last_sprint_id:
                    user_story.editable = True
                else:
                    user_story.editable = False
            else:
                user_story.editable = True
