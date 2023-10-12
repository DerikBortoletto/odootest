import time
import logging
import requests
import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from datetime import timedelta


logger = logging.getLogger(__name__)
current_date = '1970-01-01 02:46:40'
current_timestamp_1 = time.time() * 1e3
current_timestamp = 10000 * 1e3


class HubspotInstance(models.Model):
    _name = "hubspot.instance"
    _description = 'Hubspot Instance'

    def _can_play(self):
        for reg in self:
            reg.can_play = False
            crow_id = self.env.ref('hubspot.auto_sync_users_with_hubspot').sudo()
            if bool(crow_id) and bool(reg.hubspot_app_key) and not crow_id.active:
                reg.can_play = True

    can_play = fields.Boolean("Can Play", compute="_can_play", store=False)
    default_instance = fields.Boolean('Default Instance', help="Hubspot Default Instance", required=True)
    hubspot_app_key = fields.Char('Hubspot App ID', help="Hubspot Instance API key", required=True)
    name = fields.Char('Hubspot App Name', help="Hubspot Instance API Name", required=True)
    active = fields.Boolean("Active", default=True)
    force_rewrite = fields.Boolean("Force ReWrite", default=False)
    hubspot_is_import_contacts = fields.Boolean("Import Contacts", default=False)
    hubspot_is_import_skip_contacts = fields.Boolean("Import Skipped Contacts", default=False)
    hubspot_is_import_company = fields.Boolean("Import Companies", default=False)
    hubspot_is_import_skip_company = fields.Boolean("Import Skipped Companies", default=False)
    hubspot_is_export_contacts = fields.Boolean("Export Contacts", default=False)
    hubspot_is_export_company = fields.Boolean("Export Companies", default=False)
    deals = fields.Boolean("Deals", default=False)
    hubspot_is_import_deals = fields.Boolean("Import Deals", default=False)
    hubspot_is_export_deals = fields.Boolean("Export Deals", default=False)
    tickets = fields.Boolean("Tickets", default=False)
    modifiedDateForContact = fields.Char('Modified Date for Contact', default=str(current_timestamp))
    modifiedDateForCompany = fields.Char('Modified Date for Company', default=str(current_timestamp))
    modifiedDateForDeals = fields.Char('Modified Date for Deals', default=str(current_timestamp))

    all_contact = fields.Boolean("All Customers")
    all_companies = fields.Boolean("All Companies")
    all_deals = fields.Boolean("All Deals")
    
    hubspot_sync_contacts = fields.Boolean("Sync Contacts")
    hubspot_sync_companies = fields.Boolean("Sync Companies")
    hubspot_sync_deals = fields.Boolean("Sync Deals")

    hubspot_sync_task = fields.Boolean("Sync Task")
    hubspot_is_import_task = fields.Boolean("Import Task", default=False)
    hubspot_is_export_task = fields.Boolean("Export Task", default=False)
    modifiedDateForTask = fields.Char('Modified Date for Task', default=str(current_timestamp))
    all_task = fields.Boolean("All Task")

    hubspot_sync_ticket_pipeline = fields.Boolean("Sync Ticket Pipelines")
    hubspot_is_import_ticket_pipeline = fields.Boolean("Import Ticket Pipelines", default=False)
    hubspot_is_export_ticket_pipeline = fields.Boolean("Export Ticket Pipelines", default=False)
    modifiedDateForTicketPipeline = fields.Char('Modified Date for Ticket Pipelines', default=str(current_timestamp))
    all_ticket_pipelines = fields.Boolean("All Tickets Pipelines")

    hubspot_sync_ticket = fields.Boolean("Sync Ticket")
    hubspot_is_import_ticket = fields.Boolean("Import Ticket", default=False)
    hubspot_is_export_ticket = fields.Boolean("Export Ticket", default=False)
    modifiedDateForTicket = fields.Char('Modified Date for Ticket', default=str(current_timestamp))
    all_ticket = fields.Boolean("All Tickets Pipelines")
    ticket_id = fields.Char('Ticket ID')

    hubspot_sync_notes = fields.Boolean("Sync Note")
    hubspot_is_import_notes = fields.Boolean("Import Note", default=False)
    hubspot_is_export_notes = fields.Boolean("Export Note", default=False)
    modifiedDateForNotes = fields.Char('Modified Date for Note', default=str(current_timestamp))
    all_notes = fields.Boolean("All Note")

    hubspot_sync_email = fields.Boolean("Sync Email")
    hubspot_is_import_email = fields.Boolean("Import Email", default=False)
    hubspot_is_export_email = fields.Boolean("Export Email", default=False)
    modifiedDateForEmail = fields.Char('Modified Date for Email', default=str(current_timestamp))
    all_email = fields.Boolean("All Email")

    hubspot_sync_log_meeting = fields.Boolean("Sync Log Meeting")
    hubspot_is_import_log_meeting = fields.Boolean("Import Log meeting", default=False)
    hubspot_is_export_log_meeting = fields.Boolean("Export Log meeting", default=False)
    modifiedDateForlogmeeting = fields.Char('Modified Date for Log meeting', default=str(current_timestamp))
    all_log_meeting = fields.Boolean("All Log meeting")

    hubspot_sync_log_email = fields.Boolean("Sync Log Email")
    hubspot_is_import_log_email = fields.Boolean("Import Log Email", default=False)
    hubspot_is_export_log_email = fields.Boolean("Export Log Email", default=False)
    modifiedDateForLogEmail = fields.Char('Modified Date for Log Email', default=str(current_timestamp))
    all_log_email = fields.Boolean("All Log Email")

    hubspot_sync_associations = fields.Boolean("Sync Associations")
    hubspot_is_import_associations = fields.Boolean("Import Associations", default=False)
    hubspot_is_export_associations = fields.Boolean("Export Associations", default=False)
    modifiedDateForAssociations = fields.Char('Modified Date for Associations', default=str(current_timestamp))
    all_associations = fields.Boolean("All Associations")
    
    contact_field_mapping = fields.One2many('contact.field.mapping', 'hubspot_instance_id', string='Contact Field Mapping')
    company_field_mapping = fields.One2many('company.field.mapping', 'hubspot_instance_id', string='Company Field Mapping')
    deals_field_mapping = fields.One2many('deals.field.mapping', 'hubspot_instance_id', string='Deals Field Mapping')
    tickets_field_mapping = fields.One2many('tickets.field.mapping', 'hubspot_instance_id', string='Tickets Field Mapping')

    def _send_get_request(self, method):
        get_method_response = requests.get('https://api.hubapi.com' + method, headers={'Authorization': 'Bearer ' + self.hubspot_app_key})
        if get_method_response.status_code in [200, 201, 202, 203, 204]:
            if get_method_response.text:
                return get_method_response.text
        else:
            if get_method_response.text:
                # raise Warning("CONNECTION UNSUCCESSFUL")
                # raise UserError(_('111111'))
                raise UserError(_('%s', get_method_response.text))

    def _send_post_request(self, method, properties):
        post_method_response = requests.post('https://api.hubapi.com' + method, json.dumps(properties),
                                             headers={'Authorization': 'Bearer ' + self.hubspot_app_key, 'Content-Type': 'application/json'})
        if post_method_response.status_code in [200, 201, 202, 203, 204]:
            if post_method_response.text:
                return post_method_response.text
        else:
            if post_method_response.text:
                raise UserError(_('%s', post_method_response.text))

    def _send_delete_request(self, method):
        delete_method_response = requests.delete('https://api.hubapi.com' + method, headers={'Authorization': 'Bearer ' + self.hubspot_app_key})
        if delete_method_response.status_code in [200, 201, 202, 203, 204]:
            if delete_method_response.text:
                return delete_method_response.text
        else:
            if delete_method_response.text:
                raise UserError(_('%s', delete_method_response.text))

    def _send_put_request(self, method, properties):
        put_method_response = requests.put('https://api.hubapi.com' + method, json.dumps(properties),
                                           headers={'Authorization': 'Bearer ' + self.hubspot_app_key, 'Content-Type': 'application/json'})
        if put_method_response.status_code in [200, 201, 202, 203, 204]:
            if put_method_response.text:
                return put_method_response.text
        else:
            if put_method_response.text:
                raise UserError(_('%s', put_method_response.text))

    def _send_patch_request(self, method, properties):
        patch_method_response = requests.patch('https://api.hubapi.com' + method, json.dumps(properties),
                                               headers={'Authorization': 'Bearer ' + self.hubspot_app_key, 'Content-Type': 'application/json'})
        if patch_method_response.status_code in [200, 201, 202, 203, 204]:
            if patch_method_response.text:
                return patch_method_response.text
        else:
            if patch_method_response.text:
                raise UserError(_('%s', patch_method_response.text))

    def _raise_user_error(self, exception):
        raise UserError(_('%s', str(exception)))
        # if self.env.context.get('params') and self.env.context.get('params').get('model'):
        #     exception = json.loads(str(exception))
        #     if exception.get('message'):
        #         raise UserError(_('%s', str(exception.get('message'))))

    def action_import_contact_fields(self):
        return self.env['hubspot.contact.fields'].import_contact_fields(self)

    def action_import_company_fields(self):
        return self.env['hubspot.company.fields'].import_company_fields(self)

    def action_import_deals_fields(self):
        return self.env['hubspot.deals.fields'].import_deals_fields(self)

    def action_import_tickets_fields(self):
        return self.env['hubspot.ticket.fields'].import_ticket_fields(self)

    @api.onchange('hubspot_sync_contacts')
    def _onchange_hubspot_sync_contacts(self):
        if not self.hubspot_sync_contacts:
            self.hubspot_is_import_contacts = False
            self.hubspot_is_export_contacts = False

    @api.onchange('hubspot_sync_companies')
    def _onchange_hubspot_sync_companies(self):
        if not self.hubspot_sync_companies:
            self.hubspot_is_import_company = False
            self.hubspot_is_export_company = False

    @api.onchange('hubspot_sync_deals')
    def _onchange_hubspot_sync_deals(self):
        if self.hubspot_sync_deals == False:
            self.hubspot_is_import_deals = False
            self.hubspot_is_export_deals = False

    @api.onchange('hubspot_sync_task')
    def _onchange_hubspot_sync_task(self):
        if not self.hubspot_sync_task:
            self.hubspot_is_import_task = False
            self.hubspot_is_export_task = False

    @api.onchange('hubspot_sync_notes')
    def _onchange_hubspot_sync_notes(self):
        if self.hubspot_sync_notes == False:
            self.hubspot_is_import_notes = False
            self.hubspot_is_export_notes = False

    @api.onchange('hubspot_sync_email')
    def _onchange_hubspot_sync_email(self):
        if self.hubspot_sync_email == False:
            self.hubspot_is_import_email = False
            self.hubspot_is_export_email = False

    @api.onchange('hubspot_sync_log_meeting')
    def _onchange_hubspot_sync_log_meeting(self):
        if self.hubspot_sync_log_meeting == False:
            self.hubspot_is_import_log_meeting = False
            self.hubspot_is_export_log_meeting = False

    @api.onchange('hubspot_sync_log_email')
    def _onchange_hubspot_sync_log_email(self):
        if self.hubspot_sync_log_email == False:
            self.hubspot_is_import_log_email = False
            self.hubspot_is_export_log_email = False

    @api.model
    def create(self, vals):
        hubspot_instance = self.env['hubspot.instance'].search([('active', '=', True)])
        if vals['default_instance']:
            for hubspot_instance_id in hubspot_instance:
                if hubspot_instance_id.default_instance:
                    raise UserError(_('You already added default instance to another instance'))
        res = super(HubspotInstance, self).create(vals)
        return res

    def write(self, vals):
        if 'default_instance' in vals:
            hubspot_instance = self.env['hubspot.instance'].search([])
            for hubspot_instance_id in hubspot_instance:
                if not vals['default_instance']:
                    vals['default_instance'] = False
                elif hubspot_instance_id.default_instance == True:
                    raise UserError(_('You already added default instance to another instance'))
        return super(HubspotInstance, self).write(vals)

    def action_test_connection(self):
        logger.info("In action_test_connection")
        response = requests.request('GET', 'https://api.hubapi.com/owners/v2/owners', headers={'Authorization': 'Bearer ' + self.hubspot_app_key})
        if response.status_code == 200:
            return self.sendMessage("CONNECTION SUCCESSFUL")
        elif response.status_code == 401:
            return self.sendMessage("Invalid Credentials")
        else:
            raise Warning("CONNECTION UNSUCCESSFUL")

    def sendMessage(self, message):
        # view_ref = self.env['ir.model.data'].get_object_reference('hubspot', 'hubspot_message_wizard_form')
        view_ref = self.env['ir.model.data'].xmlid_to_res_id('hubspot.hubspot_message_wizard_form')
        # view_id = view_ref and view_ref[1] or False,
        # if view_id:
        return {
            'type': 'ir.actions.act_window',
            'name': 'Message',
            'res_model': 'hubspot.message.wizard',
            'view_mode': 'form',
            'view_id': view_ref,
            'context': {'message': message},
            'target': 'new',
            'nodestroy': True,
        }

    def action_import_contacts(self):
        return self.env['res.partner'].import_contacts_from_hubspot(self)

    def action_import_skip_contacts(self):
        return self.env['res.partner'].import_skip_contacts_from_hubspot(self)

    def action_import_companies(self):
        return self.env['res.partner'].import_companies_from_hubspot(self)

    def action_export_contacts(self):
        return self.env['res.partner'].export_contacts_to_hubspot(self)

    def action_import_skip_companies(self):
        return self.env['res.partner'].action_import_skip_companies(self)

    def action_export_companies(self):
        return self.env['res.partner'].export_companies_to_hubspot(self)

    def action_import_deals(self):
        return self.env['crm.lead'].import_deals_from_hubspot(self)

    def action_export_deals(self):
        return self.env['crm.lead'].export_deals_to_hubspot(self)

    def action_import_task(self):
        return self.env['mail.activity'].import_task_from_hubspot(self)

    def action_export_task(self):
        return self.env['mail.activity'].export_task_to_hubspot(self)

    def action_import_notes(self):
        return self.env['mail.message'].import_note_from_hubspot(self)

    def action_export_notes(self):
        return self.env['mail.message'].export_note_to_hubspot(self)

    def action_import_skip_notes(self):
        return self.env['mail.message'].action_import_skip_notes(self)

    def action_import_email(self):
        return self.env['mail.message'].import_email_from_hubspot(self)

    def action_export_email(self):
        return self.env['mail.message'].export_email_to_hubspot(self)

    def action_import_log_meeting(self):
        return self.env['calendar.event'].import_log_meeting_from_hubspot(self)

    def action_export_log_meeting(self):
        return self.env['calendar.event'].export_log_meeting_to_hubspot(self)

    def action_import_log_email(self):
        return self.env['mail.activity'].import_log_email_from_hubspot(self)

    def action_export_log_email(self):
        return self.env['mail.activity'].export_log_email_to_hubspot(self)

    def action_import_ticket_pipeline(self):
        return self.env['helpdesk.team'].import_pipelines_from_hubspot(self)

    def action_export_ticket_pipeline(self):
        # return self.env['helpdesk.team'].export_log_email_to_hubspot(self)
        pass

    def action_import_ticket(self):
        return self.env['helpdesk.ticket'].import_tickets_from_hubspot(self)

    def action_export_ticket(self):
        # return self.env['helpdesk.team'].export_log_email_to_hubspot(self)
        pass

    def action_active_inactive(self):
        # status_field = self.active
        if self.active == True:
            self.active = False
        elif self.active == False:
            self.active = True
        return self.active

    def action_import_users(self):
        return self.env['res.users'].syncAllUsers(self)
    
    def action_import_my_ticket(self):
        self.env['helpdesk.ticket'].get_ticket_details_and_create([self.ticket_id],self)
        
    def action_start_crow(self):
        crow_id = self.env.ref('hubspot.auto_sync_users_with_hubspot').sudo()
        if bool(crow_id):
            if not bool(crow_id.active):
                crow_id.nextcall = fields.Datetime.now() + timedelta(minutes=5)
                crow_id.active = True 


        