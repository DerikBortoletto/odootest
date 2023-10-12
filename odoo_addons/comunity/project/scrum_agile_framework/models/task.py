from odoo import models, fields, api
from datetime import timedelta

class Task(models.Model):
    _inherit = 'project.task'

    scrum_stage = fields.Selection([('todo', 'To Do'), 
                                    ('doing', 'Doing'), 
                                    ('done', 'Done')], 
                                    string='Stage of the scrum task', default='todo', group_expand='_expand_groups')

    # RELATIONAL MODELS
    project_id = fields.Many2one('project.project', string='Project', compute='_get_project_id', store=True, ondelete='cascade')
    scrum_is = fields.Boolean(string='Is Scrum', related='project_id.scrum_is',store=False)
    sprint_id = fields.Many2one('scrum_agile_framework.sprint', string='Sprint', compute='_get_sprint_id', store=True)
    user_story_id = fields.Many2one('scrum_agile_framework.user_story', string='User Story', ondelete='cascade')

    # METHODS
    @api.depends('user_story_id.sprint_id')
    def _get_sprint_id(self):
        for task in self:
            if task.user_story_id:
                task.sprint_id = task.user_story_id.sprint_id

    @api.depends('user_story_id.project_id')
    def _get_project_id(self):
        for task in self:
            if task.user_story_id:
                task.project_id = task.user_story_id.project_id

    @api.model
    def _expand_groups(self, states, domain, order):
        return ['todo', 'doing', 'done']


