import logging

from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo


_logger = logging.getLogger(__name__)


class trading_partner_users_spt(models.Model):
    _name = 'trading.partner.users.spt'
    _inherit = "custom.connector.spt"
    _inherits = {'res.partner': 'res_partner_id'}
    _description = 'partner contact'
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'partner_uuid': 'partner_uuid', 'uuid': 'uuid'}
    _TTRxToOdoo = {'uuid': 'uuid'}


    res_partner_id = fields.Many2one('res.partner', 'Trading Partner', ondelete='cascade', required=True) # Partner Linked

    # TTRx2 Fields    
    uuid = fields.Char("UUID", readonly=True, copy=False, index=True)
    created_on = fields.Datetime('Create On', readonly=True)
    last_update = fields.Datetime('Last Update', readonly=True)
    username = fields.Char('User Name')
    # parent_id = partner_uuid
    # full_name = name
    # title = title
    # email = email
    # is_active = active
    
    partner_uuid = fields.Char(compute="_compute_uuid", store=False, readonly=True)

    def _compute_uuid(self):
        for reg in self:
            reg.partner_uuid = reg.parent_id.uuid
    
    
    def FromOdooToTTRx(self, connector, values={}):
        var = super().FromOdooToTTRx(connector=connector,values=values)
        title = values.get('title') and self.env['res.partner.title'].browse(values['title']).name
        var.update({
            'tp_user_uuid': self.uuid if bool(self.uuid) else None,
            'uuid': self.parent_id.uuid,
            'full_name': values.get('name',self.name),
            'username': values.get('username',self.username),
            'title': title,
            'email': values.get('email',self.email),
            'is_active': values.get('active',self.active),
        })
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        var = super().FromTTRxToOdoo(connector=connector,values=values)
        parent_id = values.get('partner_uuid') and self.env['res.partner'].search([('uuid','=',values['partner_uuid'])], limit=1).id or None
        title = values.get('title') and self.env['res.partner.title'].search(['|',('name','ilike',values['title']),
                                                                                  ('shortcut','ilike',values['title'])],limit=1).id or None 
        var.update({
            'type': 'contact',
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': values.get('full_name'),
            'parent_id': parent_id,
            'title': title,
            'email': values.get('email'),
            'active': bool(values['active']) if bool(values.get('active')) else None
        })
        CleanDataDict(var)
        return var


    def action_send(self):
        for reg in self:
            reg.CreateInTTRx()
        return True

    def action_test(self):
        # 'location': {'location_uuid': 'location_uuid', 'tt_id': 'id'}
        self.SyncFromTTRx(self.connector_id,location_uuid='cb251f49-3276-41a6-9bda-eda4225b5811',primary_model='location')
        return True


