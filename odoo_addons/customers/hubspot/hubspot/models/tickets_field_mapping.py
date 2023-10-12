import logging
from odoo import api, fields, models, _
logger = logging.getLogger(__name__)


class TicketsFieldMapping(models.Model):
    _name = "tickets.field.mapping"
    _description = "Tickets Field Mapping"

    hubspot_instance_id = fields.Many2one('hubspot.instance')
    odoo_fields = fields.Many2one('ir.model.fields', domain=[('model_id.model', '=', 'helpdesk.ticket'), ('readonly', '!=', True)], string='Odoo Field')
    hubspot_fields = fields.Many2one('hubspot.ticket.fields', domain=[('hubspot_compute', '!=', True), ('field_type', '!=', 'calculation_equation'), ('hubspot_readonly', '!=', True)], string='Hubspot Field')
    hubspot_field_description = fields.Text("Description")

    @api.onchange('hubspot_fields')
    def _onchange_hubspot_fields(self):
        if self.hubspot_fields.description:
            self.hubspot_field_description = self.hubspot_fields.description
        if self.hubspot_fields:
            if self.hubspot_fields.field_type == 'text':
                return {'domain': {'odoo_fields': [('model_id.model', '=', 'helpdesk.ticket'), '|', ('ttype', '=', 'text'), ('ttype', '=', 'char')]}}
            if self.hubspot_fields.field_type == 'phonenumber':
                return {'domain': {'odoo_fields': [('model_id.model', '=', 'helpdesk.ticket'), ('ttype', '=', 'char')]}}
            if self.hubspot_fields.field_type == 'textarea':
                return {'domain': {'odoo_fields': [('model_id.model', '=', 'helpdesk.ticket'), ('ttype', '=', 'text')]}}
            if self.hubspot_fields.field_type == 'checkbox' or self.hubspot_fields.field_type == 'select' or self.hubspot_fields.field_type == 'radio' or self.hubspot_fields.field_type == 'booleancheckbox':
                return {'domain': {'odoo_fields': [('model_id.model', '=', 'helpdesk.ticket'), ('ttype', '=', 'selection')]}}
            if self.hubspot_fields.field_type == 'number':
                return {'domain': {'odoo_fields': [('model_id.model', '=', 'helpdesk.ticket'), ('ttype', '=', 'integer')]}}
            if self.hubspot_fields.field_type == 'date':
                return {'domain': {'odoo_fields': [('model_id.model', '=', 'helpdesk.ticket'), ('ttype', '=', 'date')]}}

    @api.onchange('odoo_fields')
    def _onchange_odoo_fields(self):
        for rec in self:
            if rec.odoo_fields:
                if rec.odoo_fields.ttype == 'char':
                    return {'domain': {'hubspot_fields': [('hubspot_instance_id', '=', self.env.context.get('hubspot_instance_id')), '|', ('field_type', '=', 'text'), ('field_type', '=', 'phonenumber')]}}
                elif rec.odoo_fields.ttype == 'text':
                    return {'domain': {'hubspot_fields': [('hubspot_instance_id', '=', self.env.context.get('hubspot_instance_id')), '|', ('field_type', '=', 'textarea'), ('field_type', '=', 'text')]}}
                elif rec.odoo_fields.ttype == 'selection':
                    return {'domain': {'hubspot_fields': [('hubspot_instance_id', '=', self.env.context.get('hubspot_instance_id')), '|', '|', '|', ('field_type', '=', 'checkbox'), ('field_type', '=', 'select'), ('field_type', '=', 'radio'), ('field_type', '=', 'booleancheckbox')]}}
                elif rec.odoo_fields.ttype == 'integer':
                    return {'domain': {'hubspot_fields': [('hubspot_instance_id', '=', self.env.context.get('hubspot_instance_id')), ('field_type', '=', 'number')]}}
                elif rec.odoo_fields.ttype == 'date':
                    return {'domain': {'hubspot_fields': [('hubspot_instance_id', '=', self.env.context.get('hubspot_instance_id')), ('field_type', '=', 'date')]}}
                else:
                    return {'domain': {'hubspot_fields': [('hubspot_instance_id', '=', self.env.context.get('hubspot_instance_id')), ('field_type', '=', '')]}}
