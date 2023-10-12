from odoo import models, fields, api
from odoo.exceptions import UserError
from ..tools import CleanDataDict, DateTimeToOdoo, DateToOdoo

class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    tracktrace_is = fields.Boolean('Is TrackTraceRx2',compute="_compute_tracktrace", readonly=True, store=False)
    location_spt_id = fields.Many2one('locations.management.spt',string='Location SPT',compute="_compute_tracktrace", readonly=True, store=False)
    storage_area_spt_id = fields.Many2one('storage.areas.spt',string='Storage Area SPT',compute="_compute_tracktrace", readonly=True, store=False)
    storage_shelf_spt_id = fields.Many2one('shelf.spt',string='Storage Shelf SPT',compute="_compute_tracktrace", readonly=True, store=False)
    connector_id = fields.Many2one('connector.spt', 'Connector')

    uuid = fields.Char('UUID', copy=False)
    status_delete_portal = fields.Boolean(copy=False, index=True)
    created_on = fields.Datetime('Create On', readonly=True, copy=False)
    last_update = fields.Datetime('Last Update', readonly=True, copy=False)
    gs1_id = fields.Char("GLN")
    gs1_sgln = fields.Char("GSI SGLN")
    location_detail = fields.Char("Location Detail")
    is_unselectable_location = fields.Boolean("Is Unselectable Location", default=False, required=True)
    is_virtual = fields.Boolean("Is Virtual Location", default=False)
    manufacturing_location_id = fields.Char("Manufacturing Location ID")
    notes = fields.Text("Notes")


    def _parent_location(self):
        location_spt_id = self.env['locations.management.spt'].search([('stock_location_id','=',self.id)],limit=1)
        while not bool(location_spt_id):
            
            location_spt_id = location_spt_id.search([('stock_location_id','=',self.id)],limit=1)
            
        
        self.env['locations.management.spt'].search([('stock_location_id','=',self.id)],limit=1)

    # @api.model
    # def create(self, vals):
    #     res = super(StockLocation, self).create(vals)
    #     created = self.CreateInTTRx(self.connector_id)
    #     # resource = "%s" % self._name
    #     # create_response = self._GetList(connector=self.connector_id, resource=resource, po_nbr=self.name)
    #
    #
    #     # self.FromOdooToTTRx(vals)
    #     x = self
    #     y = self
    #
    #     return res

    def automatic_produtos_ttrx(self):
        for i in self.env['product.template'].search([]):
            try:
                method = 'GET'
                url = f"/products/{i.ttr_uuid}"
                get_response = self.company_id.send_request_to_ttr(
                    request_url=url,
                    method=method
                )
                try:
                    if get_response['is_active'] == False:
                        try:
                            i.update({'active': False})
                        except:
                            pass
                except:
                    pass
                if not get_response:
                    i.update({'status_delete_portal': True})
            except:
                pass



    def automatic_contatos_ttrx(self):
        for i in self.env['res.partner'].search([]):
            try:
                method = 'GET'
                url = f"/trading_partners/{i.uuid}"
                get_response = self.company_id.send_request_to_ttr(
                    request_url=url,
                    method=method
                )
                try:
                    if get_response['is_active'] == False:
                        try:
                            i.update({'active': False})
                        except:
                            pass
                except:
                    pass

                if not get_response:
                    i.update({'status_delete_portal': True})
            except:
                pass

    def automatic_so_ttrx(self):
        for i in self.env['sale.order'].search([]):
            try:
                method = 'GET'
                url = f"/transactions/sales/{i.uuid}"
                get_response = self.company_id.send_request_to_ttr(
                    request_url=url,
                    method=method
                )
                if not get_response or i.no_send_to_ttr2:
                    i.update({'status_delete_portal': True})
            except:
                pass

    def automatic_locations_ttrx(self):
        for i in self.env['stock.location'].search([]):
            method = 'GET'
            url = f"/locations/{i.uuid}"
            get_response = self.company_id.send_request_to_ttr(
                request_url=url,
                method=method
            )
            if not get_response:
                try:
                    i.active = False
                except:
                    pass








    def FromOdooToTTRx(self, values={}):
        var = {}
        # if bool(values):
        name =""
        if values.get("name"):
            name= values['name']
        var.update({
            'name': name,
            'is_unselectable_location': False,
            'is_active': True
        })
        return var




    @api.model
    def create(self, values):
        res = super(StockLocation, self).create(values)
        pesquisa = self.env['stock.location'].search_count([('name','=', values['name'])])
        pesquisa_2 = self.env['stock.location'].search([('name', '=', values['name'])])
        # pesquisa_2 = self.env['stock.location'].search([('name', '=', values['name'])])
        lista = sorted(pesquisa_2.ids)
        # if len(lista) > 1:
        #     self.env['stock.location'].search([('id', '=', lista[0])]).unlink()
        if len(lista) > 1:
            pesquisa_2.browse(lista[0]).unlink()

        # if pesquisa > 1:
        #     pesquisa_2[0].unlink()
        if res.complete_name:
            if self.env['stock.location'].search_count([('complete_name', '=', res.complete_name)]) > 1:
                self.env['stock.location'].search([('complete_name', '=', res.complete_name)])[0].unlink()
        if res.complete_name == res.name:
                    request_url = "/locations"
                    method = 'POST'
                    request_data = self.FromOdooToTTRx(values)
                    post_response = res.company_id.send_request_to_ttr(request_url, request_data, method=method)

                    method = 'GET'
                    url = f"/locations/{post_response['uuid']}"
                    get_response = self.company_id.send_request_to_ttr(
                        request_url=url,
                        method=method
                    )
                    self.location_spt_id.FromTTRxToOdoo(self.env['connector.spt'].search([])[0],get_response)
                    # self.location_spt_id.FromTTRxToOdoo(self.env['connector.spt'].search([])[0], get_response)
                    # self.env['locations.management.spt'].SyncFromTTRx(self.env['connector.spt'].search([])[0])
                    res.update({
                        'uuid': get_response.get('uuid'),
                        'created_on': DateTimeToOdoo(get_response.get('created_on')),
                        'last_update': DateTimeToOdoo(get_response.get('last_update')),
                        'gs1_id': get_response.get('gs1_id'),
                        'gs1_sgln': get_response.get('gs1_sgln'),
                        'name': get_response.get('name'),
                        'location_detail': get_response.get('location_detail'),
                        'is_unselectable_location': get_response.get('is_unselectable_location'),
                        'notes': get_response.get('notes') or None,
                        'active': get_response.get('is_active'),
                        # 'location_id': location_id,
                        # 'default_address_id': default_address_id,
                        # 'location_type': location_type,
                    })
                    return res
        else:
            return res
            # print(res)
    
    def _compute_tracktrace(self):
        for reg in self:
            reg.storage_shelf_spt_id = self.env['shelf.spt'].search([('stock_location_id','=',reg.id)],limit=1)
            if bool(reg.storage_shelf_spt_id.location_id):
                reg.storage_area_spt_id = self.env['storage.areas.spt'].search([('stock_location_id','=',
                                                                                 reg.storage_shelf_spt_id.location_id.id)],limit=1)
            else:
                reg.storage_area_spt_id = self.env['storage.areas.spt'].search([('stock_location_id','=',reg.id)],limit=1)
            
            if bool(reg.storage_area_spt_id):
                storage_id = reg.storage_area_spt_id
                location_spt_id = self.env['locations.management.spt'].search([('stock_location_id','=',
                                                                                storage_id.location_id.id)],limit=1)
                while not bool(location_spt_id):
                    storage_id = self.env['storage.areas.spt'].search([('location_id','=',
                                                                                 storage_id.location_id.id)],limit=1)
                    if bool(storage_id):
                        location_spt_id = self.env['locations.management.spt'].search([('stock_location_id','=',
                                                                                storage_id.location_id.id)],limit=1)
                    else:
                        location_spt_id = self.env['locations.management.spt']
                        break
                reg.location_spt_id = location_spt_id
            else:
                reg.location_spt_id = self.env['locations.management.spt'].search([('stock_location_id','=',reg.id)],limit=1)
            
            reg.tracktrace_is = bool(reg.location_spt_id) or bool(reg.storage_area_spt_id) or bool(reg.storage_shelf_spt_id)

    def unlink(self):
        for res in self:
            uuid = res.uuid
            if res.uuid:
                uuid = res.uuid
                res.company_id.send_request_to_ttr('/locations/' + uuid, method="DELETE")
                super().unlink()
            else:
                uuid = res.location_spt_id.uuid
                res.company_id.send_request_to_ttr('/locations/' + uuid, method="DELETE")
                super().unlink()