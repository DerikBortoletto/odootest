from math import ceil

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    project_id = fields.Many2one("project.project", string="Project", ondelete="restrict",
                                 domain="[('allow_timesheets', '=', True), ('company_id', '=', company_id)]",
                                 help="Project to which the tickets (and the timesheets) will be linked by default.")

    def _create_project(self, name, allow_billable, other):
        return self.env['project.project'].create({
            'name': name,
            'type_ids': [
                (0, 0, {'name': _('In Progress')}),
                (0, 0, {'name': _('Closed'), 'is_closed': True})
            ],
            'allow_timesheets': True,
            **other,
        })

    @api.model
    def create(self, vals):
        if vals.get('use_helpdesk_timesheet') and not vals.get('project_id'):
            allow_billable = vals.get('use_helpdesk_sale_timesheet')
            vals['project_id'] = self._create_project(vals['name'], allow_billable, {}).id
        return super(HelpdeskTeam, self).create(vals)

    def write(self, vals):
        if 'use_helpdesk_timesheet' in vals:
            if not vals['use_helpdesk_timesheet']:
                vals['project_id'] = False
            elif not bool(self.project_id):
                allow_billable = vals.get('use_helpdesk_sale_timesheet')
                vals['project_id'] = self._create_project(vals.get('name',self.name), allow_billable, {}).id
        result = super(HelpdeskTeam, self).write(vals)
        for team in self.filtered(lambda team: team.use_helpdesk_timesheet and not team.project_id):
            team.project_id = team._create_project(team.name, team.use_helpdesk_sale_timesheet, {'allow_timesheets': True,})
            self.env['helpdesk.ticket'].search([('team_id', '=', team.id), ('project_id', '=', False)]).write({'project_id': team.project_id.id})
        return result

    @api.model
    def _init_data_create_project(self):
        # TODO: remove me in master
        return


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # TODO: [XBO] change this field in related and stored (to count the number of tickets per project) field to the one in helpdesk.team
    project_id = fields.Many2one("project.project", string="Project", domain="[('allow_timesheets', '=', True), ('company_id', '=', company_id)]", compute="_compute_project_id", readonly=False, store=True)
    # TODO: [XBO] remove me in master
    task_id = fields.Many2one(
        "project.task", string="Task", compute='_compute_task_id', store=True, readonly=False,
        domain="[('id', 'in', _related_task_ids)]", tracking=True,
        help="The task must have the same customer as this ticket.")
    # TODO: [XBO] remove me in master (since task_id field will be removed too)
    _related_task_ids = fields.Many2many('project.task', compute='_compute_related_task_ids')
    timesheet_ids = fields.One2many('account.analytic.line', 'helpdesk_ticket_id', 'Timesheets')
    is_closed = fields.Boolean(related="task_id.stage_id.is_closed", string="Is Closed", readonly=True)
    # TODO: [XBO] remove me in master (since task_id field will be removed too)
    is_task_active = fields.Boolean(related="task_id.active", string='Is Task Active', readonly=True)
    use_helpdesk_timesheet = fields.Boolean('Timesheet activated on Team', related='team_id.use_helpdesk_timesheet', readonly=True)
    total_hours_spent = fields.Float(compute='_compute_total_hours_spent', default=0)
    encode_uom_in_days = fields.Boolean(compute='_compute_encode_uom_in_days')
    
    def _compute_encode_uom_in_days(self):
        self.encode_uom_in_days = self.env.company.timesheet_encode_uom_id == self.env.ref('uom.product_uom_day')

    @api.depends('project_id', 'company_id')
    def _compute_related_task_ids(self):
        # TODO: [XBO] remove me in master because the task_id will be removed, then this compute and the _related_task_ids field will be useless
        for t in self:
            domain = [('project_id.allow_timesheets', '=', True), ('company_id', '=', t.company_id.id)]
            if t.project_id:
                domain = [('project_id', '=', t.project_id.id)]
            t._related_task_ids = self.env['project.task'].search(domain)._origin
    
    @api.depends('timesheet_ids')
    def _compute_total_hours_spent(self):
        for ticket in self:
            ticket.total_hours_spent = round(sum(ticket.timesheet_ids.mapped('unit_amount')), 2)
    
    @api.depends('project_id')
    def _compute_task_id(self):
        # TODO: [XBO] remove me in master (task_id field will be removed)
        with_different_project = self.filtered(lambda t: t.project_id != t.task_id.project_id)
        with_different_project.update({'task_id': False})
    
    @api.depends('team_id')
    def _compute_project_id(self):
        for ticket in self:
            ticket.project_id = ticket.team_id.project_id
    
    @api.onchange('task_id')
    def _onchange_task_id(self):
        # TODO: remove me in master
        return
    
    @api.constrains('project_id', 'team_id')
    def _check_project_id(self):
        # TODO: [XBO] see in master if we must remove this method, but since project_id will be a related field, this constrains will be useless.
        for ticket in self:
            if ticket.use_helpdesk_timesheet and not ticket.project_id and not (self.env.registry._init and self.env.context.get('module') == 'helpdesk_timesheet'):
                raise ValidationError(_("The project is required to track time on ticket."))
    
    @api.constrains('project_id', 'task_id')
    def _check_task_in_project(self):
        # TODO: [XBO] remove me in master (task_id field will be removed in master)
        for ticket in self:
            if ticket.task_id:
                if ticket.task_id.project_id != ticket.project_id:
                    raise ValidationError(_("The task must be in ticket's project."))
    
    def _get_timesheet(self):
        # Overriden in helpdesk_sale_timesheet
        return self.timesheet_ids
    
    @api.model_create_multi
    def create(self, value_list):
        team_ids = set([value['team_id'] for value in value_list if value.get('team_id')])
        teams = self.env['helpdesk.team'].browse(team_ids)
    
        team_project_map = {}  # map with the team that require a project
        for team in teams:
            if team.use_helpdesk_timesheet:
                team_project_map[team.id] = team.project_id.id
    
        for value in value_list:
            if value.get('team_id') and not value.get('project_id') and team_project_map.get(value['team_id']):
                value['project_id'] = team_project_map[value['team_id']]
    
        return super(HelpdeskTicket, self).create(value_list)
    
    def write(self, values):
        result = super(HelpdeskTicket, self).write(values)
        # force timesheet values: changing ticket's task or project will reset timesheet ones
        timesheet_vals = {}
        for fname in self._timesheet_forced_fields():
            if fname in values:
                timesheet_vals[fname] = values[fname]
        if timesheet_vals:
            for timesheet in self.sudo()._get_timesheet():
                timesheet.write(timesheet_vals)  # sudo since helpdesk user can change task
        return result
    
    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Set the correct label for `unit_amount`, depending on company UoM """
        result = super(HelpdeskTicket, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        result['arch'] = self.env['account.analytic.line']._apply_timesheet_label(result['arch'])
        return result
    
    def action_view_ticket_task(self):
        # TODO: [XBO] remove me in master (task_id field will be removed in master)
        self.ensure_one()
        return {
            'view_mode': 'form',
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'res_id': self.task_id.id,
        }
    
    def _timesheet_forced_fields(self):
        """ return the list of field that should also be written on related timesheets """
        return ['task_id', 'project_id']
    
    # def action_timer_start(self):
    #     if not self.user_timer_id.timer_start and self.display_timesheet_timer:
    #         super().action_timer_start()
    #
    # def action_timer_stop(self):
    #     # timer was either running or paused
    #     if self.user_timer_id.timer_start and self.display_timesheet_timer:
    #         minutes_spent = self.user_timer_id._get_minutes_spent()
    #         minimum_duration = int(self.env['ir.config_parameter'].sudo().get_param('hr_timesheet.timesheet_min_duration', 0))
    #         rounding = int(self.env['ir.config_parameter'].sudo().get_param('hr_timesheet.timesheet_rounding', 0))
    #         minutes_spent = self._timer_rounding(minutes_spent, minimum_duration, rounding)
    #         return self._action_open_new_timesheet(minutes_spent * 60 / 3600)
    #     return False
    #
    # def _action_open_new_timesheet(self, time_spent):
    #     return {
    #         "name": _("Confirm Time Spent"),
    #         "type": 'ir.actions.act_window',
    #         "res_model": 'helpdesk.ticket.create.timesheet',
    #         "views": [[False, "form"]],
    #         "target": 'new',
    #         "context": {
    #             **self.env.context,
    #             'active_id': self.id,
    #             'active_model': self._name,
    #             'default_time_spent': time_spent,
    #         },
    #     }
