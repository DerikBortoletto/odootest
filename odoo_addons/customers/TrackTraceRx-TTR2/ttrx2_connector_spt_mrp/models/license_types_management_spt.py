# Ajusted by Alexandre Defendi
from odoo import models, fields, api
from ..tools import CleanDataDict



class license_types_management_spt(models.Model):
    _name = 'license.types.management.spt'
    _inherit = "custom.connector.spt"
    _description = 'License Types Management'
    _order = 'name'
    _TTRxKey = "lic_id"
    _OdooToTTRx = {'lic_id': 'id'}
    _TTRxToOdoo = {'id': 'lic_id'}
    
    lic_id = fields.Char("Database ID", copy=False)
    name = fields.Char("Name", required=True)
    code = fields.Char("Code", copy=False)
    valid_from = fields.Date("Valid From")
    valid_to = fields.Date("Valid To")
    is_always_expires = fields.Boolean('Is Always Expires')
    is_require_attachement = fields.Boolean('Is Require Attachment')
    is_territorial = fields.Boolean("Is Territorial")
    
    def FromOdooToTTRx(self, values={}):
        var = {
            'id': values.get('lic_id',self.lic_id if bool(self.lic_id) else None),
            'code': values.get('code',self.code or None if not bool(values) else None),
            'name': values.get('name',self.name or None if not bool(values) else None),
            'valid_from': values.get('valid_from',str(self.valid_from) or None if not bool(values) else None),
            'valid_to': values.get('valid_to',str(self.valid_to) or None if not bool(values) else None),
            'is_always_expires': values.get('is_always_expires',self.is_always_expires or None if not bool(values) else None),
            'is_require_attachement': values.get('is_require_attachement',self.is_require_attachement or None if not bool(values) else None),
            'is_territorial': values.get('is_territorial',self.is_territorial or None if not bool(values) else None),
        }
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, values):
        var = {
            'lic_id': values.get('id'),
            'code': values.get('code'),
            'name': values.get('name'),
            'valid_from': values.get('valid_from'),
            'valid_to': values.get('valid_to'),
            'is_always_expires': values.get('is_always_expires'),
            'is_require_attachement': values.get('is_require_attachement'),
            'is_territorial': values.get('is_territorial'),
        }
        CleanDataDict(var)
        return var
