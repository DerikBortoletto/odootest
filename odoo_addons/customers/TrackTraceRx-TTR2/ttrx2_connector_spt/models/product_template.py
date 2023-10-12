import json
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.ttrx2_connector_spt.tools import DateTimeToOdoo, CleanDataDict

logging.basicConfig(level=logging.DEBUG, format='%(message)s | \'%(name)s:%(lineno)s\'')
_logger = logging.getLogger(__name__)
IMPORT_TYPE = ''

TTRX_PROD_ST = [
    ('AVAILABLE', 'Available'),
    ('PHASED_OUT', 'Phased Out'),
    ('NO_LONGER_STOCKED', 'No Longer Stocked'),
    ('RETIRED', 'Retired'),
]

TTRX_PROD_TP = [
    ('Pharmaceutical', 'Pharmaceutical'),
    ('Shoe', 'Shoe'),
]

TTRX_DOSAGE = [
    ('adv', 'Advantage Vial'),
    ('amp', 'Ampule'),
    ('bag', 'Bag'),
    ('btl', 'Bottle'),
    ('cpl', 'Caplets'),
    ('cap', 'Capsules'),
    ('crm', 'Cream'),
    ('drp', 'Drops'),
    ('inh', 'Inhalant'),
    ('inj', 'Injection'),
    ('liq', 'Liquid'),
    ('ont', 'Ointment'),
    ('pwd', 'Powder'),
    ('sdv', 'Single Dose Vial'),
    ('sol', 'Solution'),
    ('sup', 'Suppository'),
    ('syg', 'Syringe'),
    ('tab', 'Tablets'),
    ('vl', 'Vial')
]

TTRX_GENDER = [
    ('men', 'Men'),
    ('women', 'Women'),
    ('unisex', 'Unisex')
]


class product_template(models.Model):
    _inherit = 'product.template'

    is_tracktrace_product = fields.Boolean("TrackTraceRx2", default=False)
    ttr_uuid = fields.Char("UUID")
    created_on = fields.Datetime('Create On')
    last_update = fields.Datetime('Updated On')
    long_name = fields.Char('Long Name')
    composition = fields.Text('Composition')
    description = fields.Text('description')
    notes = fields.Text('Notes')
    pack_size = fields.Char('Pack Size')
    pack_size_type_id = fields.Many2one('pack.size.type.spt', 'Pack Size Type')
    # TODO Check Why it's upper case, should be equal the API
    status = fields.Selection(TTRX_PROD_ST, default="AVAILABLE", string='Status')

    product_type = fields.Selection(TTRX_PROD_TP, string='Custom Product Type', default='Pharmaceutical')

    gs1_company_prefix = fields.Char("GS1 Company Prefix")
    gs1_id = fields.Char("GS1 ID")
    upc = fields.Char("UPC")
    manufacturer_id = fields.Many2one(comodel_name='manufacturers.spt', string='Manufacturer')
    product_requirement_ids = fields.Many2many(comodel_name='product.requirement.spt',
                                               relation='res_requirement_template_rel', column1='iid', column2='pid',
                                               string='Requirements')
    product_identifier_ids = fields.Many2many(comodel_name='product.identifier.spt',
                                              relation='res_identifier_template_rel', column1='iid', column2='pid',
                                              string='Identifiers')
    generic_name = fields.Char('Generic Name')
    strength = fields.Char('Strength')
    dosage_form = fields.Selection(TTRX_DOSAGE, default="adv", string='Form')

    us_size = fields.Char('Shoe Size')
    gender = fields.Selection(TTRX_GENDER, default="men", string='Gender')

    thrid_party_logistic_provide_id = fields.Many2one('thrid.party.logistic.provide.spt', 'Third Party Logistic')
    product_packaging_ids = fields.Many2many('product.packaging.spt', 'res_packaging_template_rel', 'ppid', 'pid',
                                             string='Packaging')
    error_text = fields.Text(string="Log", track_visibility="onchange")
    url_config = fields.Boolean('URL', compute='_compute_url', store=True)
    status_delete_portal = fields.Boolean()
    import_type = fields.Char("import type", default="New")
    gtin14 = fields.Char("GTIN14")

    product_spt_id = fields.Many2one(
        comodel_name="product.spt",
        string='Related to TTRX2 product',
        compute="_compute_ttrx_product"
    )
    identifier_duns = fields.Char(
        related="product_spt_id.identifier_duns",
        string="DUNS Code")
    identifier_hin = fields.Char(
        related="product_spt_id.identifier_hin",
        string="HIN Code")
    identifier_us_dea = fields.Char(
        related="product_spt_id.identifier_us_dea",
        string="US DEA Code")
    identifier_us_ndc = fields.Char(
        related="product_spt_id.identifier_us_ndc",
        string="US NDC Code")
    identifier_br_cnes = fields.Char(
        related="product_spt_id.identifier_br_cnes",
        string="BR CNES Code")
    identifier_br_cnjp = fields.Char(
        related="product_spt_id.identifier_br_cnjp",
        string="BR CNPJ Code")
    identifier_br_cpf = fields.Char(
        related="product_spt_id.identifier_br_cpf",
        string="BR CPF Code")
    identifier_br_profegnbr = fields.Char(
        related="product_spt_id.identifier_br_profegnbr",
        string="BR Profeg NBR Code")
    identifier_ca_din = fields.Char(
        related="product_spt_id.identifier_ca_din",
        string="CA DIN Code")

    def _OdooToTTRx(self, values={}):
        # category_id = values.get('category_id') and self.env['product.category'].search([('id','=',values['category_id'])],limit=1). or False
        # country_id = values.get('country_id') and self.env['res.count ry'].search([('id','=',values['country_id'])],limit=1).code or self.country_id.code
        var = {
            'ttr_uuid': values.get('ttr_uuid', self.ttr_uuid if bool(self.ttr_uuid) else None),
            'created_on': values.get('created_on', str(self.created_on)),
            'last_update': values.get('last_update', str(self.last_update)),
            'long_name': values.get('long_name', self.long_name),
            # 'composition': values.get('',self.composition),
            # 'description': values.get('',self.),
            'notes': values.get('notes', self.notes),
            'pack_size': values.get('pack_size', self.pack_size),
            'status': values.get('status', self.status),
            'product_type': values.get('product_type', self.product_type),
            'gs1_company_prefix': values.get('gs1_company_prefix', self.gs1_company_prefix),
            'gs1_id': values.get('gs1_id', self.gs1_id),
            'upc': values.get('upc', self.upc),
            'sku': values.get('default_code', self.default_code),
            'generic_name': values.get('generic_name', self.generic_name),
            'strength': values.get('strength', self.strength),
            'dosage_form': values.get('dosage_form', self.dosage_form),
            'us_size': values.get('us_size', self.us_size),
            'gender': values.get('gender', self.gender),
            'error_text': values.get('error_text', self.error_text),
            'url_config': values.get('url_config', self.url_config),
            'import_type': values.get('import_type', self.import_type),
            'is_active': values.get('active', self.active),
            'gtin14': values.get('gtin14', self.gtin14),

            # 'category_id': self.categ_id.tt_id or None,
            # thrid_party_logistic_provide_id = fields.Many2one('thrid.party.logistic.provide.spt', 'Third Party Logistic')
            # product_packaging_ids = fields.Many2many('product.packaging.spt', 'res_packaging_template_rel', 'ppid', 'pid', string='Packaging')
            # 'manufacturer_id' = fields.Many2one(comodel_name='manufacturers.spt', string='Manufacturer')
            # 'pack_size_type_id' = fields.Many2one('pack.size.type.spt', 'Pack Size Type')
            # product_requirement_ids = fields.Many2many(comodel_name='product.requirement.spt', relation='res_requirement_template_rel', column1='iid', column2='pid', string='Requirements')
            # product_identifier_ids = fields.Many2many(comodel_name='product.identifier.spt', relation='res_identifier_template_rel', column1='iid', column2='pid', string='Identifiers')
        }

        CleanDataDict(var)
        return var

    def _TTRxToOdoo(self, values):
        # license_type_id = values.get('license_type') and self.env['license.types.management.spt'].search([('lic_id','=',values['license_type'])],limit=1) or None
        # country_id = values.get('market') and self.env['res.country'].search([('code','=',values['market'])],limit=1) or None
        var = self.env['product.product'].search([('product_tmpl_id', '=', self.id)]).id
        res = self.env['product.spt'].search([('product_id', '=', var)])
        var = {
            'tt_id': values.get('id'),
            'created_on': DateTimeToOdoo(values['created_on']),
            'last_update': DateTimeToOdoo(values['last_update']),
            'name': values.get('name'),
            'gs1_id': values.get('gs1_id'),
            'gs1_company_id': values.get('gs1_company_id'),
            'gs1_sgln': values.get('gs1_sgln'),
            'trading_partner_uuid': values.get('trading_partner_uuid'),
            'sender_id': values.get('sender_id'),
            'receiver_id': values.get('receiver_id'),
            'as2_id': values.get('as2_id'),
            'is_delegated_serial_generation': values.get('as2_id'),
            'remote_serial_source_uuid': values.get('as2_id'),
            'remote_serial_source_name': values.get('as2_id'),
            # 'license_type': license_type_id,
            # 'country_id': country_id,
        }
        CleanDataDict(var)
        return var

    @api.depends('company_id')
    def _compute_url(self):
        if self.env.user.company_id.ttrx_api_url:
            self.url_config = True

    # def _compute_import_type(self):
    #     _logger.info("DEBUG 89: Que horas roda isso?")
    #     self.import_type = ''

    @api.onchange('gs1_company_prefix')
    def onchange_gs1_company_prefix_(self):
        if self.gs1_id:
            len_gs1 = len(self.gs1_id) + len(self.gs1_company_prefix)
            if not len_gs1 == 13:
                raise UserError("Gs1 and Gs1 company prefix should be length of 13 digit")

    @api.onchange('gs1_id')
    def onchange_gs1_id_(self):
        if self.gs1_company_prefix:
            len_gs1 = len(self.gs1_id) + len(self.gs1_company_prefix)
            if not len_gs1 == 13:
                raise UserError("Gs1 and Gs1 company prefix should be length of 13 digit")

    @api.onchange('upc')
    def onchange_upc(self):
        if self.upc:
            self.upc = self.upc

    @api.onchange('ttr_uuid')
    def _compute_ttrx_product(self):
        if self.ttr_uuid:
            product_id = self.env['product.spt'].search([('uuid', '=', self.ttr_uuid)])
            self.product_spt_id = product_id

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            if not self.long_name:
                self.long_name = self.name
            if not self.description:
                self.description = self.name

    def prepare_vals_for_export(self):
        self.ensure_one()
        identifiers = []
        # TODO : packaging

        for one in self.product_identifier_ids:
            identifiers.append(
                {
                    'identifier_code': one.code,
                    'value': one.identifier_value
                }
            )

        if not self.upc and self.upc:
            self.upc = self.upc

        request_vals = {
            'type': self.product_type or None,
            'gs1_company_prefix': self.gs1_company_prefix or None,
            'gs1_id': self.gs1_id or None,
            'upc': self.upc or None,
            'sku': self.default_code or None,
            'category_id': self.categ_id.tt_id or None,
            # Todo corrigir status de acorodo com aceitos pelo portal
            # 'status': self.status or None,
            'status': "AVAILABLE",
            'manufacturer_id': self.manufacturer_id.tt_id or None,
            'is_active': 'true' if self.active else 'false',
            "product_descriptions": json.dumps([
                {
                    "language_code": "en",
                    "name": self.name or None,
                    "description": self.description or None,
                    "composition": self.composition or None,
                    "product_long_name": self.long_name or None
                }
            ]),
            'product_identifiers': json.dumps(identifiers),
            'pack_size': self.pack_size or None,
            'pack_size_type_id': self.pack_size_type_id.tt_id or None,
            'notes': self.description or None,
        }
        return request_vals

    def update_record_on_ttr(self):
        self.ensure_one()
        _logger.info("DEBUG 172: inside criar o produto no Odoo")
        _logger.info("DEBUG 173: self.import_type = " + self.import_type)
        if self.import_type != 'import_product':
            request_vals = self.prepare_vals_for_export()
            request_vals['product_uuid'] = self.ttr_uuid
            request_vals['update_product_descriptions'] = 'true'
            request_vals['update_product_identifiers'] = 'true'
            request_vals['update_requirements'] = 'true'
            request_vals['update_packaging'] = 'true'
            ttr_uuid = ""
            # if not self.ttr_uuid:
            ttr_uuid = self._get_ttr_uuid()
            response = self.company_id.send_request_to_ttr('/products/' + self.ttr_uuid, request_vals, method="PUT")
            if response:
                if 'error' in response and response['error']:
                    _logger.info("DEBUG 188: ENTROU NO PRIMEIRO ERRO")
                    # TODO create a log when fail
                    if 'code' in response and str(response['code']).strip() == "TTBO_PRODUCT_IDENTIFIER-G00210":
                        # TODO NEED to find a way when have more than one identifier
                        _logger.error('*' * 200)
                        _logger.error(response['code'])
                        _logger.error(response['message'])
                        _logger.error(response['details'])
                        _logger.error('*' * 200)
                        request_vals['update_product_identifiers'] = False
                        if 'product_identifiers' in request_vals:
                            request_vals.pop('product_identifiers')
                        response = self.company_id.send_request_to_ttr('/products/' + self.ttr_uuid, request_vals,
                                                                       method="PUT")

                    if 'code' in response and str(response['code']).strip() == "TT2CORE__LIB__APILIB-V00920":
                        _logger.error('*' * 200)
                        _logger.error(response['code'])
                        _logger.error(response['message'])
                        _logger.error(response['details'])
                        _logger.error('*' * 200)
                        if 'manufacturer_id' in request_vals:
                            request_vals.pop('manufacturer_id')
                        response = self.company_id.send_request_to_ttr('/products/' + self.ttr_uuid, request_vals,
                                                                       method="PUT")

                    if 'error' in response and response['error']:
                        _logger.error("An error to be checked")
                        _logger.error(response)
                        response_message = 'Error not available check with TTRX team'
                        if 'message' in response and response['message']:
                            response_message = response['message']
                        response_code = 'No Code'
                        if 'code' in response and response['code']:
                            response_code = response['code']
                        _logger.error('*' * 200)
                        # TODO MUST RETURN THE RAISE HERE!!
                        # raise UserError(response_message + " " + response_code)
                        _logger.error(response_message + " " + response_code)
                        _logger.error('*' * 200)

                self.env.cr.execute(
                    "update product_template set ttr_uuid ='%s' where id=%s" % (response.get('uuid'), self.id))
                # self.ttr_uuid = response.get('uuid')
            return response

    def _get_ttr_uuid(self):

        var = self.env['product.product'].search([('product_tmpl_id', '=', self.id)]).id
        res = self.env['product.spt'].search([('product_id', '=', var)]).uuid
        if res:
            return res
        return ""
    def write(self, vals):
        """ Write Method

        :TODO check the decorator @api.model
        :param vals: The values to update the database
        :type vals: dict
        :return: the Object wrote
        :rtype: product_template
        """
        recorded_val = None
        if "type" in vals:
            vals.update({'type': 'product'})
        _logger.info("DEBUG 240: Entrou no Write")
        res = super(product_template, self).write(vals)
        _logger.info(repr(res))
        if isinstance(vals, dict):
            recorded_val = vals
        ttr_uuid = ""
        # if not self.ttr_uuid:
        ttr_uuid = self._get_ttr_uuid()
        if res and recorded_val and self.ttr_uuid and self.import_type != 'import_product' and (
                'import_types' not in recorded_val or recorded_val.get('import_types')):
            _logger.info("DEBUG: vai chamar o update no portal")
            self.update_record_on_ttr()

        return res

    @api.model
    def create(self, values):
        _logger.info("DEBUG 242: inside criar o produto no Odoo")
        _logger.info("DEBUG 243: self.import_type = " + str(self.import_type))
        if 'import_type' in values and values['import_type']:
            _logger.info("DEBUG 248: Entrou no self.import_type = 'import_product'")
            self.import_type = 'import_product'.strip()
        _logger.info("DEBUG 250: " + type(self.import_type).__name__)
        _logger.info("DEBUG 251: self.import_type = " + str(self.import_type))
        name = values.get('name')
        search = self.search([('name', '=', name)])
        if not bool(search):
            res = super(product_template, self).create(values)
        # self.product_spt_id.create(values)
        if 'import_type' in self and self.import_type == 'import_product' or values.get(
                'import_type') == 'import_product':
            _logger.info("DEBUG 257: Entrou no correto")
            request_vals = res.prepare_vals_for_export()
            res.company_id.send_request_to_ttr('/products', request_vals, method="POST")
            return res
        else:
            _logger.info("DEBUG 260: Entrou no errado")
            if res.company_id.ttrx_api_url:
                request_vals = res.prepare_vals_for_export()
                if not res.company_id.api_key or type(res.company_id.api_key) != 'str':
                    """The company ID is not load in the product saved
                    we get the Company object from the actual user self.env.user.company_id
                    Other alternative is use the Search:
                        company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
                    """
                    res.company_id = self.env.user.company_id

                response = res.company_id.send_request_to_ttr('/products', request_vals, method="POST")
                if response.get('message'):
                    raise UserError(response.get('message'))
                res.ttr_uuid = response.get('uuid')
                self._cr.commit()
                if res.ttr_uuid:
                    res.error_text = "Product created successfully in TTR2"
                    _logger.info("Product created successfully in TTR2")
            return res

    def create_product(self, product):
        # TODO The POST in portal should be the last one!
        identifier_obj = self.env['product.identifier.spt']
        manufacturers_obj = self.env['manufacturers.spt']
        identifier_ids_list = None
        # TODO Create Category, Composition, form, etc
        if product:
            # product_in_base = self.search([('ttr_uuid', '=', product['uuid'])], limit=1)
            manufacturer_id = None
            # TODO: Verificar
            # if product['manufacturer_id']:
            #     manufacturer = manufacturers_obj.create_manufacturer(product['manufacturer_id'])
            #
            #     if manufacturer:
            #         manufacturer_id = manufacturer['id']

            if product['identifier_us_ndc']:
                identifier_ids_list = identifier_obj.create_identifier(
                    {'code': 'us_ndc',
                     'identifier_value': product['identifier_us_ndc'],
                     })
            tmp_notes = product['long_name']
            if 'notes' in product and product['notes']:
                tmp_notes = product['notes']
            vals = {
                'name': product['name'],
                'description': product['description'],
                'ttr_uuid': product['uuid'],
                'product_type': product['type_name'],
                'gs1_company_prefix': product['gs1_company_prefix'],
                'gs1_id': product['gs1_id'],
                # 'manufacturers_id': manufacturer_id,#TODO: Verificar
                'upc': product['upc'],
                'default_code': product['sku'],
                'status': str(product['status']).upper(),
                'is_tracktrace_product': True,
                'notes': tmp_notes,
                'pack_size': product['pack_size'],
                'long_name': product['long_name'],
                'composition': product['composition'],
                'type': 'product',
                'tracking': 'serial',
                'import_type': 'import_product',
                'product_identifier_ids': identifier_ids_list
            }
            prod = self.create(vals)
            return prod

    def update_product(self, product):
        # TODO The POST in portal should be the last one!
        identifier_obj = self.env['product.identifier.spt']
        manufacturers_obj = self.env['manufacturers.spt']
        identifier_ids_list = None
        # TODO Create Category, Composition, form, etc
        if product:
            manufacturer_id = None
            if product['manufacturer_id']:
                manufacturer = manufacturers_obj.create_manufacturer(product['manufacturer_id'])

                if manufacturer:
                    manufacturer_id = manufacturer['id']

            if product['identifier_us_ndc']:
                identifier_ids_list = identifier_obj.create_identifier(
                    {'code': 'us_ndc',
                     'identifier_value': product['identifier_us_ndc'],
                     })
            tmp_notes = product['long_name']
            if 'notes' in product and product['notes']:
                tmp_notes = product['notes']
            vals = {
                'name': product['name'],
                'description': product['description'],
                'ttr_uuid': product['uuid'],
                'product_type': product['type_name'],
                'gs1_company_prefix': product['gs1_company_prefix'],
                'gs1_id': product['gs1_id'],
                'manufacturers_id': manufacturer_id,
                'upc': product['upc'],
                'default_code': product['sku'],
                'status': str(product['status']).upper(),
                'is_tracktrace_product': True,
                'notes': tmp_notes,
                'pack_size': product['pack_size'],
                'long_name': product['long_name'],
                'composition': product['composition'],
                'import_type': 'import_product',
                'type': 'product',
                'tracking': 'serial',
                'use_expiration_date': True,
                'expiration_time': 365,
                'product_identifier_ids': identifier_ids_list
            }
            prod = self.write(vals)
            return prod

    def unlink(self):
        for res in self:
            uuid = res._get_ttr_uuid()
            if res.ttr_uuid:
                uuid = res.ttr_uuid
                res.company_id.send_request_to_ttr('/products/' + uuid, method="DELETE")
                super().unlink()
            else:
                res.company_id.send_request_to_ttr('/products/' + uuid, method="DELETE")
                super().unlink()
            # self.env['sync.product.spt.wizard'].search([]).action_process()



