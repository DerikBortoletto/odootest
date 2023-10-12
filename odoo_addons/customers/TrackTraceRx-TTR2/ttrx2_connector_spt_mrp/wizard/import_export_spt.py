import json
import logging
import urllib.error
import urllib.request as urllib2
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)




class import_export_spt(models.TransientModel):
    _name = 'import.export.spt'
    _description = 'Import Export Wizard'
    
    res_company_id = fields.Many2one('res.company', 'Company')
    
    # TrackTraceRx to Odoo #
    import_trading_partners = fields.Boolean('Import Trading Partners')
    sync_trading_partners_addresses = fields.Boolean('Sync Trading Partners Addresses')
    sync_trading_partners_licenses = fields.Boolean('Sync Trading Partners Licenses')
    sync_trading_partners = fields.Boolean('Sync Trading Partners')
    
    # Products #
    import_product = fields.Boolean('Import Products')
    import_pack_size_type = fields.Boolean('Import Pack Size Type')
    import_identifier = fields.Boolean('Import Identifiers')
    # sync_trading_partners_licenses = fields.Boolean('Sync Trading Partners Licenses')
    # sync_trading_partners = fields.Boolean('Sync Trading Partners')
    
    # Company Management #
    license_type = fields.Boolean('License Type')
    product_requirement = fields.Boolean('Product Requirement')
    location_management = fields.Boolean('Location Management')
    
    # Manufacturer Management #
    import_manufacturer = fields.Boolean('Import Manufacturer')
    import_categories = fields.Boolean('Import Categories')
    
    # Order / Shipment Management #
    import_shipment = fields.Boolean('Import Shipments')
    
    # somente para no groups
    import_license = fields.Boolean('Import License')
    
    
    
    def import_export(self):
        for record in self:
            key = record.res_company_id.api_key
            error_log_obj = self.env['tracktrace.log.spt']
            res_partner_obj = self.env['res.partner']
            res_partner_add_obj = self.env['trading.partner.address.spt']
            res_partner_lic_obj = self.env['license.spt']
            product_template_obj = self.env['product.template']
            sale_order_obj = self.env['sale.order']
            json_res = None
            json_res_data = None
            
            url = record.res_company_id.ttrx_api_url
            
            if record.import_trading_partners:
                _logger.info("DEBUG 165: Enter on Import Manufacturer")
                self.env['res.partner'].SyncTTRx(company=record.res_company_id)

            
            if record.import_manufacturer:
                _logger.info("DEBUG 175: Enter on Import Manufacturer")
                self.env['manufacturers.spt'].SyncTTRx(company=record.res_company_id)
            
            if record.import_product:
                self.env['product.spt'].SyncTTRx(company=record.res_company_id)
            #     _logger.info("DEBUG 123: Enter on Import Product")
            #     try:
            #         request = urllib2.Request(url + '/products', headers={'authorization': record.res_company_id.api_key})
            #         response_body = urllib2.urlopen(request).read()
            #         json_res = json.loads(response_body.decode('utf-8'))
            #     except urllib.error.HTTPError as e:
            #         error_log_obj.create({
            #             'create_date': datetime.today(),
            #             'message': json.loads(e.read().decode('utf-8')).get('message'),
            #         })
            #         _logger.error(str(error_log_obj))
            #     json_res_data = json_res.get('data')
            #     if json_res_data:
            #         for one_pro in json_res_data:
            #             _logger.info("Product UUID: " + one_pro['uuid'] + "Name: " + one_pro['name'])
            #             product_template_obj['import_type'] = 'import_product'
            #             # Here we will decide if we will create or update
            #             product_in_base = product_template_obj.search([('ttr_uuid', '=', one_pro['uuid'])], limit=1)
            #             if product_in_base:
            #                 _logger.info("Found the product: " + str(one_pro['uuid']))
            #                 product_in_base.import_type = 'import_product'
            #                 one_pro['import_type'] = 'import_product'
            #                 product_in_base.update_product(one_pro)
            #                 _logger.info("Product Updated: " + str(product_in_base.id))
            #             else:
            #                 _logger.info("Product not Found: " + str(one_pro['uuid']))
            #                 prod_created = product_template_obj.create_product(one_pro)
            #                 _logger.info("Product Created: " + str(prod_created.id))
            #             del product_in_base
            #             _logger.info("_" * 200)
            
            # if record.import_shipment:
            #     _logger.info("DEBUG 150: Enter on Import Shipment")
            #     try:
            #         request = urllib2.Request(url + '/shipments', headers={'authorization': record.res_company_id.api_key})
            #         response_body = urllib2.urlopen(request).read()
            #         json_res = json.loads(response_body.decode('utf-8'))
            #     except urllib.error.HTTPError as e:
            #         error_log_obj.create({
            #             'create_date': datetime.today(),
            #             'message': json.loads(e.read().decode('utf-8')).get('message'),
            #         })
            #     json_res_data = json_res.get('data')
            #     if json_res_data:
            #         for order in json_res_data:
            #             uuid = order['uuid']
            #             sale_order_obj.create_sale_order(uuid, url, key)
            
            # if record.license_type:
            #     _logger.info("DEBUG 169: Enter on Import License")
            #     self.env['license.types.management.spt'].SyncTTRx(company=record.res_company_id)
            # if record.product_requirement:
            #     _logger.info("DEBUG 172: Enter on Import requirements")
            #     self.env['product.requirement.spt'].SyncTTRx(company=record.res_company_id)
            # if record.import_pack_size_type:
            #     _logger.info("DEBUG 178: Enter on Import Pack Size")
            #     self.env['pack.size.type.spt'].sync_product_type(company=record.res_company_id)
            if record.location_management:
                _logger.info("DEBUG 181: Enter on Import location")
                self.env['locations.management.spt'].SyncTTRx(company=record.res_company_id)
                # self.env['locations.management.spt'].sync_location_store_areas_with_ttc(company=record.res_company_id)
            # if record.import_categories:
            #     _logger.info("DEBUG 185: Enter on Import Categories")
            #     self.env['product.category'].sync_categories(company=record.res_company_id)
            # if record.import_identifier:
            #     _logger.info("DEBUG 188: Enter on Import Identifiers")
            #     self.env['product.identifier.spt'].sync_product_identifier(company=record.res_company_id)
            # if record.import_license:
            #     self.env['license.spt'].SyncTTRxLocation(company=record.res_company_id,location_uuid='9611de79-b30a-4684-8a4c-53121fcad21d')
            
            self._cr.commit()
            
            if (self.user_has_groups('base.group_no_one')):
                raise UserError('xxxxx')
