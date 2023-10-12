from odoo import models, fields, api
from odoo.exceptions import UserError





class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    location_detail = fields.Char("Location Detail")
    uuid = fields.Char('UUID')
    storage_uuid = fields.Char('Storage UUID')
    gs1_id = fields.Char("GLN")
    manufacturing_location_id = fields.Char("Manufacturing Location ID")
    is_unselectable = fields.Boolean("Is Unselectable Location", default=True)
    storage_area_ids = fields.One2many('stock.location', 'location_id', string="Storage Area")
    storage_id = fields.Many2one('stock.location')
    sub_location_ids = fields.One2many('stock.location', 'location_id', string="Sub Location")
    sub_location_id = fields.Many2one('stock.location')
    is_storage = fields.Boolean('Is Storage')
    is_sub_location = fields.Boolean('Is Storage')
    properties = fields.Selection([
        ('COLD', 'Cold storage'),
        ('FROZEN', 'Frozen storage'),
        ('RESTRICTED_ACCESS', ' High security/Restricted Access')], string='Properties', default='COLD')
    
    connector_id = fields.Many2one('connector.spt', 'Connector')
   
    
    # address_partner = fields.Many2many('res.partner',"location_partner_rel","location_id","partner_id")
    # address_ids = fields.One2many('trading.partner.address.spt', 'location_id', 'Addresses')
    # sub_location_ids = fields.One2many('stock.location','location_id','Sub Locations')
    # license_ids = fields.One2many('license.spt', 'location_id', 'Licenses')
    # storage_areas_ids = fields.One2many('storage.areas.spt', 'location_id', 'Storage Areas')
    # read_points_ids = fields.One2many('read.points.spt', 'location_id', 'Read Points')
    
    
    
    # def sync_locations_with_ttc(self,company=False):
    #     if not company:
    #         return False
    #     response = company.send_request_to_ttr('/locations', {})
    #     self.create_update_locations(response.get('data'), company=company)
    #     return True
    #
    
    # def create_update_locations(self, datas, company=False):
    #     for data in datas:
    #         if data.get('uuid') and self.search([('uuid','=',data.get('uuid'))]):
    #             self.create(data)
    #         else:
    #             return False
    #     return True
    
    # @api.onchange('is_storage')
    # def location_id_onchange(self):
    #     print("")
    #     if self.is_storage == True:
    #         if self.storage_id:
    #             self.location_id = self.storage_id
    #
    #
    # @api.onchange('storage_area_ids')
    # def storage_area_ids_onchange(self):
    #     for line in self.storage_area_ids:
    #         line.update({
    #             'is_storage':True,
    #             'is_unselectable':False,
    #         })
    # if self.storage_area_ids:
    #     self.storage_id = True
    
    
    def send_request_for_address_export_or_update(self):
        # for line in self.address_partner:
        # for address_rec in self.trading_partner_address_spt_ids.filtered(lambda x: not x.ttr_uuid):
        address_vals = {
            'uuid': self.uuid,
            # 'address_gs1_id': self.gs1_id or None,
            'address_nickname': self.partner_id.name,
            'recipient_name': self.partner_id.name,
            'line1': self.partner_id.street,
            # 'line2': address_rec.line2 or None,
            # 'line3': address_rec.line3 or None,
            # 'line4': address_rec.line4 or None,
            'country_code': "US",
            # 'state': address_rec.res_country_state_id.name or None,
            'city': self.partner_id.city,
            # 'zip': address_rec.zip or None,
            # 'phone': address_rec.phone or None,
            # 'phone_ext': address_rec.phone_ext or None,
            # 'email': address_rec.email or None,
            # 'address_ref': address_rec.address_re 'name': line.get('name'),f or None,
        }
        if address_vals:
            self.company_id.send_request_to_ttr('/locations/' + self.uuid + '/addresses', address_vals, method="POST")
            # address_rec.write({'uuid': address_response.get('uuid')})
            self._cr.commit()
        return True
    
    
    
    def prepare_vals_for_location_export(self):
        self.ensure_one()
        if self.location_id.usage == 'view':
            parent_id = None
        else:
            parent_id = self.location_id
        request_vals = {
            'name': self.name,
            'parent_location_uuid': parent_id,
            'is_unselectable_location': self.is_unselectable or None,
            'gs1_id': self.gs1_id or None,
            'is_active': "True",
            'manufacturing_location_prefix_or_suffix_id_value': self.manufacturing_location_id or None
        }
        return request_vals
    
    
    
    @api.model
    def create(self, values):
        res = super(StockLocation, self).create(values)
        if res.company_id.ttrx_api_url:
            for record in res:
                request_vals = record.prepare_vals_for_location_export()
                if request_vals:
                    response = record.company_id.send_request_to_ttr('/locations', request_vals, method="POST")
                    record.uuid = response.get('uuid')
                    # TODO fix all access to protected member
                    record._cr.commit()
                    if record.uuid:
                        self.error_text = "Location created successfully in TTR2"
                    for sub in res.sub_location_ids:
                        if sub:
                            sub_location_vals = {
                                'name': sub.name,
                                'parent_location_uuid': record.uuid,
                                'is_unselectable_location': sub.is_unselectable or None,
                                'gs1_id': sub.gs1_id or None,
                                'is_active': "True",
                                'manufacturing_location_prefix_or_suffix_id_value': self.manufacturing_location_id or None
                            }
                            response = sub.company_id.send_request_to_ttr('/locations', sub_location_vals,
                                                                          method="POST")
                            sub.uuid = response.get('uuid')
                    
                    for storage in res.storage_area_ids:
                        if storage:
                            if storage.is_storage:
                                request_vals = {
                                    'uuid': record.uuid,
                                    'name': storage.name,
                                    'properties': storage.properties,
                                    'is_storage_conditions_verification_disabled': "false",
                                    'is_active': "true",
                                }
                                uuid = record.uuid
                                response = record.company_id.send_request_to_ttr(
                                    '/locations/' + uuid + '/storage_areas', request_vals, method="POST")
                                storage.storage_uuid = response.get('uuid')
        return res
    
    
    
    def vals_update_sublocation(self, values):
        if values.get('sub_location_ids'):
            for sub_loc in self.sub_location_ids.filtered(lambda x: not x.is_storage):
                if not sub_loc.uuid:
                    sub_location_vals = {
                        'name': sub_loc.name,
                        'parent_location_uuid': self.uuid,
                        'is_unselectable_location': True,
                        'gs1_id': sub_loc.gs1_id,
                        'is_active': "True",
                        'manufacturing_location_prefix_or_suffix_id_value': self.manufacturing_location_id or None
                    }
                    company = sub_loc.company_id
                    response = company.send_request_to_ttr('/locations', sub_location_vals, method="POST")
                    sub_loc.write({'uuid': response.get('uuid')})
        return True
    
    
    
    def vals_update_storagelocation(self, values):
        if values.get('storage_area_ids'):
            for storage_loc in self.storage_area_ids.filtered(lambda x: x.is_storage):
                if not storage_loc.storage_uuid:
                    storage_location_vals = {
                        'uuid': self.uuid,
                        'name': storage_loc.name,
                        'properties': storage_loc.properties,
                        'is_storage_conditions_verification_disabled': "false",
                        'is_active': "true",
                    }
                    company = storage_loc.company_id
                    uuid = self.uuid
                    response = company.send_request_to_ttr('/locations/' + uuid + '/storage_areas',
                                                           storage_location_vals, method="POST")
                    storage_loc.write({'storage_uuid': response.get('uuid')})
        return True
    
    
    
    def prepare_vals_for_update_location(self, values):
        self.ensure_one()
        if not values.get('storage_area_ids') and not values.get('sub_location_ids'):
            request_vals = {
                'uuid': self.uuid,
                'name': self.name,
                'is_unselectable_location': self.is_unselectable or None,
                'gs1_id': self.gs1_id or None,
                'is_active': "True",
                'manufacturing_location_prefix_or_suffix_id_value': self.manufacturing_location_id or None
            }
            company = self.company_id
            uuid = self.uuid
            response = company.send_request_to_ttr('/locations/' + uuid, request_vals, method="PUT")
            self.write({'uuid': response.get('uuid')})
        return True
    
    
    
    
    def write(self, values):
        res = super(StockLocation, self).write(values)
        if not values.get('uuid'):
            if self.uuid:
                self.vals_update_sublocation(values)
                self.vals_update_storagelocation(values)
                self.prepare_vals_for_update_location(values)
        return res
    
    
    
    def unlink(self):
        for res in self:
            company = res.company_id
            if res.uuid:
                if res.sub_location_ids:
                    for line in res.sub_location_ids:
                        if not line.sub_location_ids.is_storage:
                            raise UserError("Delete will not perform as this Location has sub location.")
                else:
                    vals = {
                        'uuid': res.uuid
                    }
                    uuid = res.uuid
                    # TODO check this variable response = company.send_request_to_ttr('/locations/' + uuid, vals, method="DELETE")
                    company.send_request_to_ttr('/locations/' + uuid, vals, method="DELETE")
            
            if res.is_storage:
                if res.storage_uuid:
                    vals = {
                        'uuid': res.location_id.uuid,
                        'storage_area_uuid': res.storage_uuid,
                    }
                    uuid = res.location_id.uuid
                    storage_area_uuid = res.storage_uuid
                    response = company.send_request_to_ttr(
                        '/locations/' + uuid + '/storage_areas/' + storage_area_uuid, vals,
                        method="DELETE")
                    if response.get('message'):
                        raise UserError(response.get('message'))
        return super(StockLocation, self).unlink()
