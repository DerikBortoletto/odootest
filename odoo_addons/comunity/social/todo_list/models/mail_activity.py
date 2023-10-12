
from datetime import timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class MailActivity(models.Model):
    _name = 'mail.activity'
    _inherit = ['mail.activity', 'mail.thread']
    _rec_name = 'summary'

    date_deadline = fields.Date('Due Date', index=True, required=True, default=fields.Date.context_today, store=True)
    user_id = fields.Many2one('res.users', string='user', index=True, tracking=True, default=lambda self: self.env.user)
    res_model_id = fields.Many2one( 'ir.model', 'Document Model', index=True, ondelete='cascade', required=True,
                                    default=lambda self: self.env.ref('todo_list.model_activity_general'))
    res_id = fields.Many2oneReference(string='Related Document ID', index=True, required=True, model_field='res_model',
                                      default=lambda self: self.env.ref('todo_list.general_activities'))
    priority = fields.Selection([('0', 'Normal'), ('1', 'Important'), ('2', 'Very Important'), ('3', 'Urgent'),], 
                                default='0', index=True, store=True)
    recurring = fields.Boolean(string="Recurring", store=True)
    state = fields.Selection([('today', 'Today'), ('planned', 'Planned'), ('done', 'Done'), ('overdue', 'Expired'),
                              ('cancel', 'Cancelled'), ], 'State', compute='_compute_state', store=True)
    interval = fields.Selection([('Daily', 'Daily'), ('Weekly', 'Weekly'), ('Monthly', 'Monthly'), ('Quarterly', 'Quarterly'),('Yearly', 'Yearly')],
                                string='Recurring Interval')
    new_date = fields.Date(string="Next Due Date", store=True)

    res_model_id_name = fields.Char(related="res_model_id.name", string="Origin", readonly=True)
    duration = fields.Float(related="calendar_event_id.duration", readonly=True)
    calendar_event_id_start = fields.Datetime(related="calendar_event_id.start", readonly=True)
    calendar_event_id_partner_ids = fields.Many2many(related="calendar_event_id.partner_ids", readonly=True)
    related_model_instance = fields.Reference(selection="_selection_related_model_instance", compute="_compute_related_model_instance", string="Document")

    @api.depends("res_id", "res_model")
    def _compute_related_model_instance(self):
        for record in self:
            ref = False
            if record.res_id:
                ref = "{},{}".format(record.res_model, record.res_id)
            record.related_model_instance = ref

    @api.model
    def _selection_related_model_instance(self):
        models = self.env["ir.model"].search([("is_mail_activity", "=", True)])
        return [(model.model, model.name) for model in models]

    def action_done(self):
        """Function done button"""
        self.write({'state': 'done'})
        if self.recurring:
            self.env['mail.activity'].create({
                'res_id': self.res_id,
                'res_model_id': self.res_model_id.id,
                'summary': self.summary,
                'priority': self.priority,
                'date_deadline': self.new_date,
                'recurring': self.recurring,
                'interval': self.interval,
                'activity_type_id': self.activity_type_id.id,
                'new_date': self.get_date(),
                'user_id': self.user_id.id
            })

    def get_date(self):
        """ function for get new due date on new record"""
        date_deadline = self.new_date if self.new_date else self.date_deadline
        new_date = False
        if self.interval == 'Daily':
            new_date = (date_deadline + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif self.interval == 'Weekly':
            new_date = (date_deadline + timedelta(days=7)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif self.interval == 'Monthly':
            new_date = (date_deadline + timedelta(days=30)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif self.interval == 'Quarterly':
            new_date = (date_deadline + timedelta(days=90)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif self.interval == 'Yearly':
            new_date = (date_deadline + timedelta(days=365)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        return new_date

    @api.onchange('interval', 'date_deadline')
    def onchange_recurring(self):
        """ function for show new due date"""
        self.new_date = False
        if self.recurring:
            self.new_date = self.get_date()

    def action_date(self):
        """ Function for automated actions for deadline"""
        today = fields.date.today()
        dates = self.env['mail.activity'].search([('state', 'in', ['today', 'planned']),('date_deadline', '=', today),('recurring', '=', True)])

        dates = self.env['mail.activity'].search([('state', 'in', ['today', 'planned']),('date_deadline', '=', today),('recurring', '=', True)])
        for rec in dates:
            self.env['mail.activity'].create({
                'res_id': rec.res_id,
                 'res_model_id': rec.res_model_id.id,
                 'summary': rec.summary,
                 'priority': rec.priority,
                 'interval': rec.interval,
                 'recurring': rec.recurring,
                 'date_deadline': rec.new_date,
                 'new_date': rec.get_date(),
                 'activity_type_id': rec.activity_type_id.id,
                 'user_id': rec.user_id.id
             })
            rec.state = 'done'

    def action_cancel(self):
        """ function for cancel button"""
        return self.write({'state': 'cancel'})

    def open_origin(self):
        self.ensure_one()
        vid = self.env[self.res_model].browse(self.res_id).get_formview_id()
        response = {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "view_mode": "form",
            "res_id": self.res_id,
            "target": "current",
            "flags": {"form": {"action_buttons": False}},
            "views": [(vid, "form")],
        }
        return response

    @api.model
    def action_activities_board(self):
        action = self.env.ref("todo_list.open_boards_activities").read()[0]
        return action

    @api.model
    def _find_allowed_model_wise(self, doc_model, doc_dict):
        doc_ids = list(doc_dict)
        allowed_doc_ids = (self.env[doc_model].with_context(active_test=False).search([("id", "in", doc_ids)]).ids)
        return {
            message_id
            for allowed_doc_id in allowed_doc_ids
            for message_id in doc_dict[allowed_doc_id]
        }

    @api.model
    def _find_allowed_doc_ids(self, model_ids):
        ir_model_access_model = self.env["ir.model.access"]
        allowed_ids = set()
        for doc_model, doc_dict in model_ids.items():
            if not ir_model_access_model.check(doc_model, "read", False):
                continue
            allowed_ids |= self._find_allowed_model_wise(doc_model, doc_dict)
        return allowed_ids

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # Rules do not apply to administrator
        if self.env.is_superuser():
            return super(MailActivity, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

        ids = super(MailActivity, self)._search(args, offset=offset, limit=limit, order=order, count=False, access_rights_uid=access_rights_uid)
        if not ids and count:
            return 0
        elif not ids:
            return ids

        # check read access rights before checking the actual rules
        super(MailActivity, self.with_user(access_rights_uid or self._uid)).check_access_rights("read")

        model_ids = {}

        self.flush(["res_id", "res_model_id", "res_model"])
        for sub_ids in self._cr.split_for_in_conditions(ids):
            self._cr.execute(
                """
                SELECT DISTINCT a.id, im.id, im.model, a.res_id
                FROM "%s" a
                LEFT JOIN ir_model im ON im.id = a.res_model_id
                WHERE a.id = ANY (%%(ids)s)"""
                % self._table,
                dict(ids=list(sub_ids)),
            )
            for a_id, _ir_model_id, model, model_id in self._cr.fetchall():
                model_ids.setdefault(model, {}).setdefault(model_id, set()).add(a_id)

        allowed_ids = self._find_allowed_doc_ids(model_ids)

        final_ids = allowed_ids

        if count:
            return len(final_ids)
        else:
            # re-construct a list based on ids, because set didn't keep order
            id_list = [a_id for a_id in ids if a_id in final_ids]
            return id_list

class ActivityGeneral(models.Model):
    _name = 'activity.general'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
