import json
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from ..tools import DateTimeToOdoo, CleanDataDict


TTRX_GENDER = [
    ('men', 'Men'),
    ('women', 'Women'),
    ('unisex', 'Unisex')
]

class products_types_spt(models.Model):
    _name = 'products.types.spt'
    _inherit = "custom.connector.spt"
    _description = "List of Product Types"
    _TTRxKey = 'value'
    _order = 'name'
    _OdooToTTRx = {'value':'value'}
    
    value = fields.Char('Class', copy=False, required=True)
    name = fields.Char('Name', copy=False, required=True)

    def FromTTRxToOdoo(self, connector, values):
        var = {
            'value': values.get('class'),
            'name': values.get('name'),
        }
        CleanDataDict(var)
        return var

class products_status_spt(models.Model):
    _name = 'products.status.spt'
    _inherit = "custom.connector.spt"
    _description = "List of Product Status"
    _TTRxKey = 'name'
    _order = 'name'
    _OdooToTTRx = {'value':'value'}
    
    value = fields.Char('Value', copy=False, required=True)
    name = fields.Char('Name', copy=False, required=True)

    def FromTTRxToOdoo(self, connector, values):
        var = {
            'value': values.get('value'),
            'name': values.get('name'),
        }
        CleanDataDict(var)
        return var



class product_spt(models.Model):
    _name = 'product.spt'
    _inherit = ['custom.connector.spt','mail.thread', 'mail.activity.mixin']
    _description = "TTRx2 Product"
    _inherits = {'product.product': 'product_id'}
    _TTRxKey = 'uuid'
    _OdooToTTRx = {'uuid':'uuid'}
    _TTRxToOdoo = {'uuid':'uuid'}


    product_id = fields.Many2one('product.product', 'Product', auto_join=True, index=True, ondelete="cascade", required=True)
    

    # TTR2 Fields
    uuid = fields.Char("UUID", copy=False)
    created_on = fields.Datetime('Create On', readonly=True)
    last_update = fields.Datetime('Last Update', readonly=True)
    long_name = fields.Char('Long Name')
    gs1_company_prefix = fields.Char("GS1 Company Prefix")
    gs1_id = fields.Char("GS1 ID")
    gtin14 = fields.Char("GTIN 14")
    composition = fields.Text("Composition")
    upc = fields.Text(
        string="Unique Product Code"
    )

    
    state_id = fields.Many2one('products.status.spt', string='Status')
    manufacturer_id = fields.Many2one(comodel_name='manufacturers.spt', string='Manufacturer')

    description_ids = fields.One2many('product.description.spt','product_spt_id',string="Descriptions")
    packaging_ids = fields.One2many('product.packaging.spt','product_spt_id', string="Packgings")
    identifier_ids = fields.One2many('product.identifier.spt','product_spt_id', string='Identifiers')
    
    requirement_ids = fields.Many2many('product.requirement.spt', 'product_requirement_product_paroduct_rel', 
                                        'product_requirement_ids', 'product_product_ids', 'Requirement')

    # requirement_ids - Não tem link 
    generic_name = fields.Char('Generic Name')
    strength = fields.Char('Strength')
    dosage_form_id = fields.Many2one('pharma.dosage.forms.spt', string='Dosage Form')
    us_size = fields.Char('US Size')
    gender = fields.Char('Gender')

    pack_size = fields.Char('Pack Size')
    pack_size_type_id = fields.Many2one('pack.size.type.spt', 'Pack Size Type')

    is_leaf_product = fields.Boolean('Is leaf')
    
    product_type_id = fields.Many2one('products.types.spt', string='Custom Product Type', required=True)
    product_type_name = fields.Char('Name', related="product_type_id.name", store=False, readonly=True)
    
    identifier_duns = fields.Char(string="DUNS Code")
    identifier_hin = fields.Char(string="HIN Code")
    identifier_us_dea = fields.Char(string="US DEA Code")
    identifier_us_ndc = fields.Char(string="US NDC Code")
    identifier_br_cnes = fields.Char(string="BR CNES Code")
    identifier_br_cnjp = fields.Char(string="BR CNPJ Code")
    identifier_br_cpf = fields.Char(string="BR CPF Code")
    identifier_br_profegnbr = fields.Char(string="BR Profeg NBR Code")
    identifier_ca_din = fields.Char(string="CA DIN Code")

    # ===== TTRX2 / Product (notebook record) / Several page ===== #
    
    # The fields below, according to Julia are about product/batch based serialization shipment
    # These fields, in TTRX2 Portal are located into the Product Record / page "Several"
    # It seems that these fields will store:
    # 1 - store the serialization history of product shipments
    # 2 - its related field into TTRX2 Portal is configured to select one value of the several avaliable
    # 2.1 - The main focus of the selection process is to select the serial number related to the variable

    is_send_copy_outbound_shipments_to_2nd_party = fields.Boolean(
        string="Is send copy outbound shipments to 2nd party"
    )
    copy_outbound_shipment_to_custom_2nd_party = fields.Many2one(
        comodel_name="copy.outbound.shipment.to.custom.2nd.party",
        string="Copy outbound shipment to custom 2nd party"
    )
    is_send_copy_epcis_commission_and_decommission = fields.Boolean(
        string="Is send copy epics commission and decommission"
    )
    # Analyse to format to Many2one relation if the API response returns
    # an object to this variable into product dictionary (fields.Many2One())
    # Are those fields related to a list of outbound records, or only to one type?
    # Example, this field needs to store the outbound history of product?
    copy_epcis_commission_and_decommission_custom_2nd_party = fields.Many2one(
        comodel_name='copy.epcis.commission.and.decommission.custom.2nd.party',
        string="Epcis Commission and Decommission"
    )
    is_send_copy_epcis_aggregation_and_disaggregation = fields.Boolean(
        string="Is send copy epics aggregation and disaggregation"
    )
    # Analyse to format to Many2one relation if the API response returns
    # an object to this variable into product dictionary (fields.Many2One())
    copy_epcis_aggregation_and_disaggregation_custom_2nd_party = fields.Many2one(
        comodel_name='copy.epcis.aggregation.and.disaggregation.custom.2nd.party',
        string="Epcis Aggregation and Disaggregation"
    )
    is_leaf_product = fields.Boolean(
        string="Is leaf product"
    )
    # Analyse to format to Many2one relation if the API response returns
    # an object to this variable into product dictionary (fields.Many2One())
    format_of_copy_outbound_shipment_to_custom_2nd_party = fields.Many2one(
        comodel_name='format.of.copy.outbound.shipment.to.custom.2nd.party'
        ,string="Epcis Aggregation and Disaggregation"
    )
    is_override_products_packaging_type_validation = fields.Boolean(
        string="Is override products packaging type validation"
    )
    
    # ===== TTRX2 / Product (notebook record) / Several page ===== #

    def FromOdooToTTRx(self, connector, values={}):
        var = super(product_spt, self).FromOdooToTTRx(connector=connector,values=values)

        product_type_id = self.product_type_id.value
        category_id = self.categ_id.tt_id
        status = values.get('state_id') and self.env['products.status.spt'].browse(values['state_id']).value or self.state_id.value
        manufacturer = values.get('manufacturer_id') and self.env['manufacturers.spt'].browse(values['manufacturer_id']) or self.manufacturer_id
        manufacturer_id = manufacturer.tt_id
        manufacturer_default_address_uuid = manufacturer.address_partner_id.uuid
        dosage_form = values.get('dosage_form_id') and self.env['pharma.dosage.forms.spt'].browse(values['dosage_form_id']).tt_id or self.dosage_form_id.tt_id
        
        descriptions = []
        if not bool(values) or bool(values.get('description')) or bool(values.get('composition')) or bool(values.get('name')):
            var = {
                "language_code": "en",
                "name": values.get("name",self.name),
                "description": values.get("description",self.description),
                "composition": values.get("composition",self.composition),
            }
            descriptions.append(var)

        pack_size_type_id = values.get('pack_size_type_id') and self.env['pack.size.type.spt'].browse(values['pack_size_type_id']).tt_id or self.pack_size_type_id.tt_id
        requirements = self.requirement_ids.ids
        
        identifiers = None  # manipulate by using the API calls
        packaging = None  # manipulate by using the API calls
        composition = None  # manipulate by using the API calls
        
        # Treatment of data BEFORE send to TTRX - IMPORTANT! Validate if there Odoo does overwrite data, critical!
        # If Odoo can overwrite data stored into TTRX, this must trait to not overwrite the TTRX Version of the product!!!
        var.update({
            'type': product_type_id,
            'product_uuid': values.get('uuid',self.uuid if bool(self.uuid) else None),
            'gs1_company_prefix': values.get('gs1_company_prefix',self.gs1_company_prefix) or None,
            'gs1_id': values.get('gs1_id',self.gs1_id) or None,
            'barcode': values.get('upc',self.upc),
            #TODO checar se contiuará utilizando este field
            # 'upc': values.get('barcode',self.barcode),
            'upc': values.get('upc',self.upc),
            'sku': values.get('default_code',self.default_code),
            # Todo checar de para de categories
            # 'category_id': category_id,
            'status': status,
            'manufacturer_id': manufacturer_id or None,
            'manufacturer_default_address_uuid': manufacturer_default_address_uuid or None,
            'is_active': values.get('active', self.active),
            'update_product_descriptions': bool(descriptions) if bool(values) else None,
            'product_descriptions': json.dumps(descriptions) if bool(descriptions) else None,
            'update_product_identifiers': bool(identifiers) if bool(values) else None,
            'product_identifiers': json.dumps(identifiers) if bool(identifiers) else None,
            'update_requirements': bool(requirements) if bool(values) else None,
            'requirements': json.dumps(requirements) if bool(requirements) else None,
            'update_composition': bool(composition) if bool(values) else None,
            'composition': composition if bool(composition) else None,
            'update_packaging': bool(packaging) if bool(values) else None,
            'packaging': json.dumps(packaging) if bool(packaging) else None,
            'pack_size': values.get('pack_size', self.pack_size),
            'pack_size_type_id': pack_size_type_id,
            'notes': values.get('description_purchase', self.description_purchase),
            'class_pharmaceutical__strength': values.get('strength',self.strength) if product_type_id == 'Pharmaceutical' else None,
            'class_pharmaceutical__dosage_form': dosage_form if product_type_id == 'Pharmaceutical' else None,
            'class_pharmaceutical__generic_name': values.get('generic_name',self.generic_name) if product_type_id == 'Pharmaceutical' else None,
            'class_shoe__us_size': values.get('us_size',self.us_size) if product_type_id == 'Shoe' else None,
            'class_shoe__gender': values.get('gender',self.gender) if product_type_id == 'Shoe' else None,
            'is_send_copy_outbound_shipments_to_2nd_party': None,
            'copy_outbound_shipment_to_custom_2nd_party': None,
            'format_of_copy_outbound_shipment_to_custom_2nd_party': None,
            'is_leaf_product': values.get('is_leaf_product', self.is_leaf_product if not bool(values) else None),
            'is_override_products_packaging_type_validation': None,
            'woodfield_product_record_id': None,
            'gtin14': values.get('gtin14', self.gtin14) or None,
            
            # Identifiers relation treatment
            'identifier_duns': values.get('identifier_duns', self.identifier_duns),
            'identifier_hin': values.get('identifier_hin', self.identifier_hin),
            'identifier_us_dea': values.get('identifier_us_dea', self.identifier_us_dea),
            'identifier_us_ndc': values.get('identifier_us_ndc', self.identifier_us_ndc),
            'identifier_br_cnes': values.get('identifier_br_cnes', self.identifier_br_cnes),
            'identifier_br_cnjp': values.get('identifier_br_cnjp', self.identifier_br_cnjp),
            'identifier_br_cpf': values.get('identifier_br_cpf', self.identifier_br_cpf),
            'identifier_br_profegnbr': values.get('identifier_br_profegnbr', self.identifier_br_profegnbr),
            'identifier_ca_din': values.get('identifier_ca_din', self.identifier_ca_din),
        })
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        def _index_value(key):
            if bool(specialized_properties):
                for indx in specialized_properties:
                    if indx['key'] == key:
                        return indx['value']
            return None

        for i in self.env['product.template'].search([]):
            method = 'GET'
            url = f"/products/{i.ttr_uuid}"
            get_response = self.company_id.send_request_to_ttr(
                request_url=url,
                method=method
            )
            if not get_response:
                i.update({'status_delete_portal': True})

        
        var = super(product_spt, self).FromTTRxToOdoo(connector, values)

        description = {}
        if bool(values.get('descriptions')):
            description.update(values['descriptions'][0])

        specialized_properties = values.get('specialized_properties')
        
        dosage_form_id = self.env['pharma.dosage.forms.spt'].search([('code','=',_index_value('dosage_form'))],limit=1).id or None
        state_id = values.get('status') and self.env['products.status.spt'].search([('value','=',values['status'])],limit=1).id or None
        product_type_id = values.get('type_class') and self.env['products.types.spt'].search([('value','=',values['type_class'])],limit=1).id or None
        # product_type_id = values.get('type_class') and self.env['products.types.spt'].SyncFromTTRx(connector, uuid=values['parent_uuid'])

        var.update({
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': description['name'] if bool(description) else None,
            'type': 'product',
            'description': description['description'] if bool(description) else None,
            'composition': description['composition'] if bool(description) else None,
            'long_name': description['product_long_name'] if bool(description) else None,
            'gs1_company_prefix': values.get('gs1_company_prefix'),
            'gs1_id': values.get('gs1_id'),
            'upc': values.get('upc') if bool(values.get('upc')) else False,
            'default_code': values.get('sku'),
            'categ_id': values.get('category_id'), 
            'state_id': state_id,
            'product_type_id': product_type_id,
            'manufacturer_id': values.get('manufacturer_default_address'),
            # 'description_ids': values.get('description') if bool(values.get('description')) else None,
            'packaging_ids': values.get('packaging'),
            # 'product_identifiers': values.get('identifiers'),
            'requirement_ids': values.get('requirements'),
            # 'composition_ids': values.get('composition'),
            'strength': _index_value('strength'),
            'dosage_form_id': dosage_form_id,
            'generic_name': _index_value('generic_name'),
            'us_size': _index_value('us_size'),
            'gender': _index_value('gender'),
            'pack_size': values.get('pack_size'),
            'pack_size_type_id': values.get('pack_size_type_id') or None,
            'description_purchase': values.get('notes'),
            'active': values.get('is_active'),
            'is_leaf_product': values.get('is_leaf_product'),
            'gtin14': values.get('gtin14'),
            'tracking': 'lot',

            # Identifiers relation treatment
            'identifier_duns': values.get('identifier_duns'),
            'identifier_hin': values.get('identifier_hin'),
            'identifier_us_dea': values.get('identifier_us_dea'),
            'identifier_us_ndc': values.get('identifier_us_ndc'),
            'identifier_br_cnes': values.get('identifier_br_cnes'),
            'identifier_br_cnjp': values.get('identifier_br_cnjp'),
            'identifier_br_cpf': values.get('identifier_br_cpf'),
            'identifier_br_profegnbr': values.get('identifier_br_profegnbr'),
            'identifier_ca_din': values.get('identifier_ca_din'),            
            
            # Boolean and EPICS relation treatment
            # 'is_active':True,
            'is_send_copy_outbound_shipments_to_2nd_party': values.get('is_send_copy_outbound_shipments_to_2nd_party'),
            'copy_outbound_shipment_to_custom_2nd_party': values.get('copy_outbound_shipment_to_custom_2nd_party'),
            'is_send_copy_epcis_commission_and_decommission': values.get('is_send_copy_epcis_commission_and_decommission'),
            'copy_epcis_commission_and_decommission_custom_2nd_party': values.get('copy_epcis_commission_and_decommission_custom_2nd_party'),
            'is_send_copy_epcis_aggregation_and_disaggregation': values.get('is_send_copy_epcis_aggregation_and_disaggregation'),
            'copy_epcis_aggregation_and_disaggregation_custom_2nd_party': values.get('copy_epcis_aggregation_and_disaggregation_custom_2nd_party'),
            'is_leaf_product':True,
            'format_of_copy_outbound_shipment_to_custom_2nd_party': values.get('format_of_copy_outbound_shipment_to_custom_2nd_party'),
            'is_override_products_packaging_type_validation': values.get('is_override_products_packaging_type_validation'),
        })
        CleanDataDict(var)
        # print("Product SPT: ", var)
        return var

    def BeforeCreateInTTRx(self, **params):
        if self.type == 'product':
            return True
        else:
            return False

    def BeforeCreateFromTTRx(self, connector, response, data):
        if bool(response.get('category')) and bool(response['category'].get('id')):
            data['categ_id'] = self.env['product.category'].SyncFromTTRx(connector,id=response['category']['id']).id
        if not bool(data.get('categ_id')):
            data['categ_id'] = self.env['product.category'].search([('parent_id','=',False)],order='id',limit=1).id
        if bool(response.get('manufacturer')) and bool(response['manufacturer'].get('id')):
            data['manufacturer_id'] = self.env['manufacturers.spt'].SyncFromTTRx(connector,id=response['manufacturer']['id']).id
        return True
                
    
    def AfterCreateFromTTRx(self, connector, response, data):
        if bool(self):
            # Has Dependents
            context = dict(self.env.context or {})
            context['no_rewrite'] = True
            if bool(response.get('packaging')):
                ttr_pack_uuids = [x['uuid'] for x in response['packaging']] if bool(response.get('packaging')) else []
                pack_ids = []
                for ttr_pack_uuid in ttr_pack_uuids:
                    pack_ids += self.env['product.packaging.spt'].SyncFromTTRx(connector,product_uuid=self.uuid,
                                                                                packaging_uuid=ttr_pack_uuid,
                                                                                update=False).ids
                self.with_context(context).packaging_ids = [(6,0, pack_ids)] if bool(pack_ids) else [(5,)]
            # self.product_id.product_tmpl_id.ttr_uuid = self.uuid or None
            if bool(response.get('identifiers')):
                ttr_ident_ids = [x['id'] for x in response['identifiers']] if bool(response.get('identifiers')) else []
                ident_ids = []
                for ttr_ident_id in ttr_ident_ids: 
                    ident_ids += self.env['product.identifier.spt'].SyncFromTTRx(connector,product_uuid=self.uuid,
                                                                                identifier_id=ttr_ident_id,
                                                                                update=False).ids
                self.with_context(context).identifier_ids = [(6,0, ident_ids)] if bool(ident_ids) else [(5,)]
    
        return True

    def action_send(self):
        for reg in self:
            reg.CreateInTTRx(self.connector_id)
        return True

    def action_test(self):
        self.env['product.description.spt'].TTRxSearch(self.connector_id,product_uuid='6fd1dd3b-e629-41ab-8858-5c3c881a112e',
                                                       description_language_code="en")

