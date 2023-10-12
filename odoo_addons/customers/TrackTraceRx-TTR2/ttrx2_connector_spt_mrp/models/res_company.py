import json
import logging
import urllib.error
import urllib.request
import requests
from odoo import models, fields, api



# TTRX_PROD_ENDPOINT = 'https://api.tracktraceweb.com/2.0'
# TTRX_TEST_ENDPOINT = 'https://api.test.tracktraceweb.com/2.0'
_logger = logging.getLogger(__name__)





class res_company(models.Model):
    _inherit = 'res.company'
    
    error_message = fields.Char('Error Message', readonly=True)
    is_connected = fields.Boolean('Is Connected')
    api_environment = fields.Selection([('test', 'Testing'), ('production', 'Production')], string='Environment',
                                       default='test', required=True)
    
    # Company Settings / Policies #
    api_key = fields.Char('API Key')
    auto_vacuum = fields.Boolean('Auto-Vacuumm', default=True)
    ttrx_portal_url = fields.Char('TTrx2 Url')
    ttrx_api_url = fields.Char('TTrx2 API Url',  compute="_compute_api_url", store=False)
    ttrx_api_tested = fields.Boolean('TTrx2 Tested', default=False)
    connector_id = fields.Many2one('connector.spt', 'Connector')
    

    wharehouse_ttr = fields.Many2one('stock.warehouse', string="Default Warehouse", domain=[('reception_steps','=','three_steps')])
    
    lot_number = fields.Selection([
        ('always_required', 'Always Required'),
        ('optional_to_add_inventory_required_to_sell', 'Optional to add inventory, required to sell'),
        ('always_optional', 'Always Optional')], string='Lot Number')
    
    serial_number = fields.Selection([
        ('always_required', 'Always Required'),
        ('optional_to_add_inventory_required_to_sell', 'Optional to add inventory, required to sell'),
        ('always_optional', 'Always Optional')], string='Serial Number')
    
    strict_inventory_policies = fields.Boolean('Strict Inventory Policies')
    
    edi_source = fields.Selection([
        ('require_product_reception_verification', 'Require product reception verification'),
        ('move_to_inventory_unless_lot_missing', 'Move to inventory, unless lot is missing'),
        ('move_to_inventory_unless_lot_or_serial_missing', 'Move to inventory, unless lot or serial is missing'),
        ('move_to_inventory', 'Move to inventory')], string='From EDI Source')
    epcis_source = fields.Selection([
        ('require_product_reception_verification', 'Require product reception verification'),
        ('move_to_inventory_unless_lot_missing', 'Move to inventory, unless lot is missing'),
        ('move_to_inventory_unless_lot_or_serial_missing', 'Move to inventory, unless lot or serial is missing'),
        ('move_to_inventory', 'Move to inventory')], string='From EPCIS Source')
    other_source = fields.Selection([
        ('require_product_reception_verification', 'Require product reception verification'),
        ('move_to_inventory_unless_lot_missing', 'Move to inventory, unless lot is missing'),
        ('move_to_inventory_unless_lot_or_serial_missing', 'Move to inventory, unless lot or serial is missing'),
        ('move_to_inventory', 'Move to inventory')], string='From Other Source')
    unknown_products = fields.Selection([
        ('goes_to_products_reception', 'Goes to products reception'),
        ('decline_product', 'Refuse/Decline the product'),
        ('add_product', 'Add the product to the product database'), ], string='Unknown Products')
    
    # Compute the api url
    @api.depends("api_environment")
    def _compute_api_url(self):
        configParameter = self.env["ir.config_parameter"]
        for company in self:
            if company.api_environment == 'production':
                company.ttrx_api_url = configParameter.sudo().get_param("default_tracktracerx_endpoint_prod",
                                                                        "https://api.tracktraceweb.com/2.0")
                # company.ttrx_api_url = TTRX_PROD_ENDPOINT
            else:
                company.ttrx_api_url = configParameter.sudo().get_param("default_tracktracerx_endpoint_test",
                                                                        "https://api.test.tracktraceweb.com/2.0")
                # company.ttrx_api_url = TTRX_TEST_ENDPOINT

    @api.onchange("api_environment", "api_key")
    def onchange_api_environment_key(self):
        self.ttrx_api_tested = False
        self.error_message = ''
    
    @api.model
    def send_request_to_ttr(self, request_url, request_data=None, method='GET', fresh_response=False):
        """ Send Request to API for this company
        
        This function is responsible to send the requests to **TT2 API**
        
        .. todo:: "Investigate the fresh_response parameter"
        .. todo:: make this function more efficient
        .. note:: This function should be used with all Interactions between Odoo and TT2
        
        :param request_url: specific Endpoint for the function you need
        :type request_url: string
        :param request_data: the data for this specific Endpoint could be None
        :type request_data: dict
        :param method: The HTTP Method like POST, GET, PUT, DELETE and etc DEFAULT = GET
        :type method: str
        :param fresh_response: NEED TO INVESTIGATE
        :type fresh_response: bool
        :return: A Json with uuid
        :rtype: dict|None
        """
        ConLog = self.env['tracktrace.log.spt']
        if self.ttrx_api_tested:
            if not bool(self.ttrx_api_url) or not bool(request_url) or not bool(self.api_key):
                self.ttrx_api_tested = False
                return None
        
            temp_api_key = self.api_key
            # if not temp_api_key or type(temp_api_key) != 'str':
            #     # company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
            #     temp_api_key = self.env.user.company_id.api_key
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'Authorization': temp_api_key
            }
        
            api_url = self.ttrx_api_url + request_url
            try:
                # ConLog.addLog(method=method, message='request %s with data %s' % (api_url,str(request_data)))
                req = requests.request(method=method, url=api_url, headers=headers, data=request_data)
            except urllib.error.HTTPError as e:
                self.error_message = "Failed to test, please check your API connection key \n" + self.ttrx_api_url + '/products \n\r'
                self.error_message += e.read().decode("utf8", 'ignore')
                # ConLog.addLog(method=method, message=self.error_message, type="error")
                self.ttrx_api_tested = False
            except urllib.error.URLError as e:
                self.error_message = "Failed to test, please check your API connection key \n" + self.ttrx_api_url + '/products \n\r'
                self.error_message += e.reason
                # ConLog.addLog(method=method, message=self.error_message, type="error")
                self.ttrx_api_tested = False
            except:
                self.error_message = "Failed to connect, please check your Internet\n\r"
                self.error_message += e.reason
                # ConLog.addLog(method=method, message=self.error_message, type="error")
            # _logger.info("DEBUG 103: ")
            # _logger.info(req)
            # _logger.info(method)
            # _logger.info(api_url)
            # _logger.info(headers)
            # _logger.info(request_data)
            # _logger.info(req.status_code)
            response_text = req.text
            # ConLog.addLog(method=method, message=response_text)
            if 200 <= req.status_code <= 299:
                
                # TODO discover what is this fresh_response
                if fresh_response and response_text:
                    return response_text
            
                if req.json():
                    return req.json()
            
        return False
    
    def test_connection(self):
        """Basic Test if the connection is working
        
        :return: None
        """
        ConLog = self.env['tracktrace.log.spt']
        if self.ttrx_api_url and self.api_key:
            try:
                # ConLog.addLog(method='TEST', message="API connection test %s" % self.ttrx_api_url)
                request = urllib.request.Request(url=self.ttrx_api_url + '/products', headers={'authorization': self.api_key})
                response_body = urllib.request.urlopen(request).read()
                # json_res = json.loads(response_body.decode('utf-8'))
                self.ttrx_api_tested = True
                self.error_message = "Connection Successfully Established With TTR2"
                # ConLog.addLog(method='TEST', message=self.error_message)
            except urllib.error.HTTPError as e:
                self.error_message = "Failed to test, please check your API connection key \n" + self.ttrx_api_url + '/products \n\r'
                self.error_message += e.read().decode("utf8", 'ignore')
                self.ttrx_api_tested = False
                # ConLog.addLog(method='TEST', message=self.error_message, type="error")
            except urllib.error.URLError as e:
                self.error_message = "Failed to test, please check your API connection key \n" + self.ttrx_api_url + '/products \n\r'
                self.error_message += e.reason
                self.ttrx_api_tested = False
                # ConLog.addLog(method='TEST', message=self.error_message, type="error")
        else:
            self.error_message = 'Failed to test, you need to enter data for connection'
            self.ttrx_api_tested = False
            # ConLog.addLog(method='TEST', message=self.error_message, type="error")
    
    def import_export(self):
        """ Function to import and export as select
        
        ..todo:: Find more information about it
        
        :return: None
        
        """
        self.ensure_one()
        
        try:
            form_view = self.env.ref('tracktrace_odoo_connector_spt.import_export_form_view_spt')
        
        except ValueError:
            form_view = False
        
        return {
            'name': 'Operations',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'import.export.spt',
            'view_id': form_view,
            'views': [(form_view, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_res_company_id': self.id}
        }

    # Clears the messages and tested field when the environment or key is changed
        