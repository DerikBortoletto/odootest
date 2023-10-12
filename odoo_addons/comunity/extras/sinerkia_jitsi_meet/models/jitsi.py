from odoo import models, fields, api
from datetime import datetime, timedelta
from random import choice
import pytz


def create_hash():
    size = 32
    values = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    p = ''
    p = p.join([choice(values) for i in range(size)])
    return p

STATES_CONFERENCE={'draft': [('readonly', False)]}

class JistiMeet(models.Model):
    _name = 'sinerkia_jitsi_meet.jitsi_meet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Jitsi Meeting'
    _order = 'date desc'

    def _get_default_participant(self):
        result = []
        result.append(self.env.user.id)
        return [(6, 0, result)]

    name = fields.Char('Meeting Name', required=True, readonly=True, states=STATES_CONFERENCE)
    hash = fields.Char('Hash', readonly=True)
    date = fields.Datetime('Date', required=True, readonly=True, states=STATES_CONFERENCE, tracking=True)
    date_delay = fields.Float('Duration', required=True, default=1.0, readonly=True, states=STATES_CONFERENCE, tracking=True)
    participants = fields.Many2many('res.users', string='Participant', required=True, default=_get_default_participant, readonly=True, states=STATES_CONFERENCE, tracking=True)
    external_participants = fields.One2many('sinerkia_jitsi_meet.external_user', 'meet', string='External Participant', readonly=True, states=STATES_CONFERENCE, tracking=True)
    url = fields.Char(string='URL to Meeting', compute='_compute_url', readonly=True)
    closed = fields.Boolean('Closed', default=False, readonly=True, tracking=True)
    current_user = fields.Many2one('res.users', compute='_get_current_user', readonly=True, states=STATES_CONFERENCE)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('closed', 'Closed'),
            ('cancel', 'Cancelled'),
        ], string='Status', required=True, readonly=True, copy=False, default='draft', tracking=True)

    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.current_user = self.env.user

    @api.model
    def create(self, vals):
        vals['hash'] = create_hash()
        res = super(JistiMeet, self).create(vals)
        return res

    def action_confirm_meeting(self):
        participants = [self.current_user.partner_id.id]
        for participant in self.participants:
            participants.append(participant.partner_id.id)
        event = {
            'name': 'Alarm of Meeting %s' % self.name,
            'alarm_type': 'notification',
            'duration': 60,
        }
        data = {
            'name': 'Meeting: %s' % self.name,
            'start': self.date,
            'stop': self.date + timedelta(hours=self.date_delay),
            'allday': False,
            'location': 'Sinerkia Meet ID #%s' % self.id,
            'description': 'Meeting scheduled at the following link: %s' % self.url,
            'user_id': self.current_user.id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)], limit=1).id,
            'partner_ids': [(6, False, participants)],
            'alarm_ids': [(0,0,event)],
        }
        self.env['calendar.event'].create(data)
        
        for external_participant in self.external_participants:
            external_participant.action_sendemail()
            
        self.write({'state': 'confirmed', 'closed': False})

    def action_close_meeting(self):
        self.write({'state': 'closed', 'closed': True})

    def action_reopen_meeting(self):
        self.write({'state': 'draft', 'closed': False})

    def action_cancel_meeting(self):
        cal_event = self.env['calendar.event'].search([('res_id', '=', self.id),
                                                       ('res_model_id', '=', self.env['ir.model'].search([('model', '=', self._name)], 
                                                                                                         limit=1).id)])
        cal_event.unlink()
        self.write({'state': 'cancel', 'closed': True})

    def action_open_meeting(self):
        return {'name': 'JITSI MEET',
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': self.url
                }



    @api.model
    def _compute_url(self):
        config_url = self.env['ir.config_parameter'].sudo().get_param(
            'sinerkia_jitsi_meet.jitsi_meet_url',
            default='https://meet.jit.si/')
        for r in self:
            if r.hash and r.name:
                r.url = config_url + r.hash


class JitsiMeetExternalParticipant(models.Model):
    _name = 'sinerkia_jitsi_meet.external_user'
    _description = 'Jitsi Meeting External Participant'
    _order = 'name'

    name = fields.Char('Email', required=True)
    meet = fields.Many2one('sinerkia_jitsi_meet.jitsi_meet', string='Meeting')
    partner_id = fields.Many2one(related='meet.create_uid.partner_id')
    meeting_date = fields.Datetime(related='meet.date', string='Meeting Date')
    meeting_name = fields.Char(related='meet.name', string='Meeting Name')
    meeting_url = fields.Char(related='meet.url',string='Meeting URL')
    send_mail = fields.Boolean('Send Invitation', default=True)
    mail_sent = fields.Boolean('Invitation Sent', readonly=True, default=False)
    date_formated = fields.Char(compute='_format_date')

    def _format_date(self):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        for part in self:
            part.date_formated = datetime.strftime(
                pytz.utc.localize(part.meeting_date).astimezone(local),"%d/%m/%Y, %H:%M:%S")
            # part.date_formated = fields.Datetime.from_string(part.meeting_date).strftime('%m/%d/%Y, %H:%M:%S')
    
    def action_sendemail(self):
        for participant in self:
            if participant.send_mail:
                template = self.env.ref('sinerkia_jitsi_meet.email_template_edi_jitsi_meet')
                self.env['mail.template'].sudo().browse(template.id).send_mail(self.id)
                participant.write({'mail_sent': True})
        
