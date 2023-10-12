
from odoo import api, fields, models, _

class HelpdeskTicketMerge(models.TransientModel):
    _name = 'helpdesk.ticket.merge'
    _description = "Merge Multiple Tickets"
    


    ticket_ids = fields.Many2many('helpdesk.ticket', string="Tickets for Merge")
    user_id = fields.Many2one('res.users', string="Reassigned to", required=True)
    create_new_ticket = fields.Boolean(string='Merge and Generate New Ticket')
    target_ticket_name = fields.Char(string='New Name Ticket')
    target_helpdesk_id = fields.Many2one('helpdesk.team', string="Target Helpdesk Team")
    target_ticket_id = fields.Many2one('helpdesk.ticket', string="Merge Into Existing Ticket")

    def merge_tickets(self):
        tag_ids = self.ticket_ids.mapped('tag_ids').ids
        values = {'tag_ids': [(4, tag_id) for tag_id in tag_ids]}
        values['user_id'] = self.user_id.id
        if self.create_new_ticket:
            partner_ids = self.ticket_ids.mapped('partner_id').ids
            ticket_type_ids = self.ticket_ids.mapped('ticket_type_id').ids
            priorities = self.ticket_ids.mapped('priority')

            values.update({
                'name': self.target_ticket_name,
                'team_id': self.target_helpdesk_id.id,
                'description': self._merge_description(self.ticket_ids),
                'partner_id': len(set(partner_ids)) == 1 and partner_ids[0] or False,
                'ticket_type_id': len(set(ticket_type_ids)) == 1 and ticket_type_ids[0] or False,
                'priority': len(set(priorities)) == 1 and priorities[0] or False})

            self.target_ticket_id = self.env['helpdesk.ticket'].create(values)
        else:
            values['description'] = '\n'.join((self.target_ticket_id.description or '', self._merge_description(self.ticket_ids - self.target_ticket_id)))
            self.target_ticket_id.write(values)

        merged_tickets = self.ticket_ids - self.target_ticket_id
        self._merge_followers(merged_tickets)
        self._merge_messages(merged_tickets)
        self._merge_activity(merged_tickets)

        merged_tickets.write({'active': False})

        return {
            "type": "ir.actions.act_window",
            "res_model": "helpdesk.ticket",
            "views": [[False, "form"]],
            "res_id": self.target_ticket_id.id,
        }

    def _merge_description(self, tickets):
        return '\n'.join(tickets.mapped(lambda ticket: _("Description from ticket (#%s) %s: %s") % (str(ticket.id), ticket.name, ticket.description or _('No description'))))

    def _merge_followers(self, merged_tickets):
        self.target_ticket_id.message_subscribe(
            partner_ids=(merged_tickets).mapped('message_partner_ids').ids,
            channel_ids=(merged_tickets).mapped('message_channel_ids').ids,
        )

    def _merge_messages(self, merged_tickets):
        messages = self.env['mail.message'].search([('model','=','helpdesk.ticket'),('res_id','in',merged_tickets.ids)])
        for message in messages:
            message.res_id = self.target_ticket_id.id

    def _merge_activity(self, merged_tickets):
        activities = self.env['mail.activity'].search([('res_model','=','helpdesk.ticket'),('res_id','in',merged_tickets.ids)])
        for activity in activities:
            activity.res_id = self.target_ticket_id.id

    @api.model
    def default_get(self, fields):
        result = super(HelpdeskTicketMerge, self).default_get(fields)
        selected_tickets = self.env['helpdesk.ticket'].browse(self.env.context.get('active_ids', False))
        assigned_tickets = selected_tickets.filtered(lambda ticket: ticket.user_id)
        result.update({
            'ticket_ids': selected_tickets.ids,
            'user_id': assigned_tickets and assigned_tickets[0].user_id.id or False,
            'target_helpdesk_id': selected_tickets[0].team_id.id,
            'target_ticket_id': selected_tickets[0].id
        })
        return result

    @api.onchange('target_ticket_id')
    def _onchange_target_ticket_id(self):
        if self.target_ticket_id.user_id:
            self.user_id = self.target_ticket_id.user_id
