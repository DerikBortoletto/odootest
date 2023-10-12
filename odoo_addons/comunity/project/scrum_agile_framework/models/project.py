from odoo import models, fields, api
from datetime import timedelta


class Project(models.Model):
    _inherit = 'project.project'

    scrum_is = fields.Boolean(string='Is Scrum', default=False)
    user_story_count = fields.Integer(compute='_compute_user_story_count')
    sprint_count = fields.Integer(compute='_compute_sprint_count')
    last_sprint_id = fields.Many2one('scrum_agile_framework.sprint', compute='_get_last_sprint', store=True)

    # RELATIONAL MODELS
    sprint_ids = fields.One2many('scrum_agile_framework.sprint', 'project_id', string='Sprints')
    user_story_ids = fields.One2many('scrum_agile_framework.user_story', 'project_id', string='Product backlog')
    team_id = fields.Many2one('scrum_agile_framework.team', string='Scrum Team')
    meeting_ids = fields.One2many('scrum_agile_framework.meeting', 'project_id', string='Meeting')
    #Hay que meter stakeholders

    # METHODS
    def _compute_user_story_count(self):
        user_story_data = self.env['scrum_agile_framework.user_story'].read_group(
            [('project_id', 'in', self.ids)], ['project_id'], ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in user_story_data)
        for project in self:
            project.user_story_count = result.get(project.id, 0)

    def _compute_sprint_count(self):
        sprint_data = self.env['scrum_agile_framework.sprint'].read_group(
            [('project_id', 'in', self.ids)], ['project_id'], ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in sprint_data)
        for project in self:
            project.sprint_count = result.get(project.id, 0)

    @api.depends('sprint_ids.date_start')
    def _get_last_sprint(self):
        for project in self:
            if project.sprint_ids:
                last = project.sprint_ids.sorted(key='date_start')
                project.last_sprint_id = last[-1].id
            else:
                project.last_sprint_id = False

