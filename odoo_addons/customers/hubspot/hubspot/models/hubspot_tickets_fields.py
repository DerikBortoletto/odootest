import logging
import json
from odoo import fields, models, _
logger = logging.getLogger(__name__)


class HubspotTicketFields(models.Model):
    _name = "hubspot.ticket.fields"
    _description = "Hubspot Ticket Fields"

    name = fields.Char("Label Name", readonly=True)
    field_type = fields.Char("Field Type", readonly=True)
    technical_name = fields.Char("Technical Name", readonly=True)
    options = fields.Char('Hubspot options', readonly=True)
    description = fields.Text("Description", readonly=True)
    hubspot_instance_id = fields.Many2one('hubspot.instance', 'Hubspot Instance Name', help="Hubspot Instance Name", readonly=True, copy=False)
    hubspot_contact_fields = fields.Many2one('hubspot.instance', string='Hubspot fields', readonly=True)
    hubspot_compute = fields.Boolean("Hubspot compute", readonly=True)
    hubspot_readonly = fields.Boolean("Hubspot Readonly", readonly=True)



    def import_ticket_fields(self, hubspot_instance):
        response_tickets_properties = hubspot_instance._send_get_request('/crm/v3/properties/ticket')
        json_response_tickets_properties = json.loads(response_tickets_properties)
        try:
            for ticket_property in json_response_tickets_properties['results']:
                self.get_ticket_property_details_and_create(ticket_property, hubspot_instance)

        except Exception as e:
            error_message = '>>> Error while getting deals property in odoo \nHubspot response %s' % (str(e))
            self.env['hubspot.logger'].create_log_message('Import Deals property', error_message)
            logger.exception(">>> Error in import_ticket_fields\n" + error_message)
            hubspot_instance._raise_user_error(e)

    def get_ticket_property_details_and_create(self, ticket_property, hubspot_instance):
        ticket_property_dict = {}
        option_list = []
        if 'label' in ticket_property:
            ticket_property_dict['name'] = ticket_property['label']
        if 'name' in ticket_property:
            ticket_property_dict['technical_name'] = ticket_property['name']
        if 'fieldType' in ticket_property:
            ticket_property_dict['field_type'] = ticket_property['fieldType']
        if 'description' in ticket_property:
            ticket_property_dict['description'] = ticket_property['description']
        if 'options' in ticket_property:
            for options in ticket_property['options']:
                option_list.insert(0,(options['value'], options['label']))
                # option_list.append(options['label'])
            ticket_property_dict['options'] = option_list
        if 'calculated' in ticket_property:
            if ticket_property['calculated']:
                ticket_property_dict['hubspot_compute'] = True
            else:
                ticket_property_dict['hubspot_compute'] = False
        
        ticket_property_dict['hubspot_readonly'] = False
        if 'modificationMetadata' in ticket_property:
            if 'readOnlyValue' in ticket_property:
                if ticket_property['readOnlyValue']:
                    ticket_property_dict['hubspot_readonly'] = True
        ticket_property_dict['hubspot_instance_id'] = hubspot_instance.id
        hubspot_ticket_fields_id = self.env['hubspot.ticket.fields'].sudo().search([('technical_name', '=', str(ticket_property['name'])),('hubspot_instance_id', '=', hubspot_instance.id)], limit=1)
        if hubspot_ticket_fields_id:
            hubspot_ticket_fields_id.with_context({'from_hubspot': True}).write(ticket_property_dict)
            logger.debug(">>> Write into Existing Odoo Hubspot ticket Fields %s" % str(hubspot_ticket_fields_id.name))
        else:
            ticket_field_record = self.with_context({'from_hubspot': True}).create(ticket_property_dict)
            logger.debug(">>> Created New ticket ID %s property in Odoo" % str(ticket_field_record.id))








