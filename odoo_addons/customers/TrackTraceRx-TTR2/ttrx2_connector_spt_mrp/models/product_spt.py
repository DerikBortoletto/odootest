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

    def FromTTRxToOdoo(self, values):
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

    def FromTTRxToOdoo(self, values):
        var = {
            'value': values.get('value'),
            'name': values.get('name'),
        }
        CleanDataDict(var)
        return var



class product_spt(models.Model):
    _name = 'product.spt'
    _inherit = "custom.connector.spt"
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

    
    state_id = fields.Many2one('products.status.spt', string='Status')
    manufacturer_id = fields.Many2one(comodel_name='manufacturers.spt', string='Manufacturer')

    description_ids = fields.One2many('product.description.spt','product_spt_id',string="Descriptions")
    packaging_ids = fields.One2many('product.packaging.spt','product_spt_id', string="Packgings")
    identifier_ids = fields.One2many('product.identifier.spt','product_spt_id', string='Identifiers')
    composition_ids = fields.One2many('product.composition.spt','product_spt_id', string='BoM of Composition')
    
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
    product_type_name = fields.Char('Name', realated="product_type_id.name", store=False, readonly=True)
    

    def FromOdooToTTRx(self, values={}):
        var = super(product_spt, self).FromOdooToTTRx(values)

        product_type_id = self.product_type_id.code
        category_id = self.categ_id.tt_id
        status = values.get('state_id') and self.env['products.status.spt'].browse(values['state_id']).value or self.state_id.value
        manufacturer = values.get('manufacturer_id') and self.env['manufacturers.spt'].browse(values['manufacturer_id']) or self.manufacturer_id
        manufacturer_id = manufacturer.tt_id
        manufacturer_default_address_uuid = manufacturer_id.address_partner_id.uuid
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
        
        var.update({
            'type': product_type_id,
            'product_uuid': values.get('uuid',self.uuid if bool(self.uuid) else None),
            'gs1_company_prefix': values.get('gs1_company_prefix',self.gs1_company_prefix),
            'gs1_id': values.get('gs1_id',self.gs1_id),
            'upc': values.get('bar_code',self.barcode),
            'sku': values.get('default_code',self.default_code),
            'category_id': category_id,
            'status': status,
            'manufacturer_id': manufacturer_id,
            'manufacturer_default_address_uuid': manufacturer_default_address_uuid,
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
            'gtin14': values.get('gtin14', self.gtin14),
        })
        CleanDataDict(var)
        return var
    
    def FromTTRxToOdoo(self, values):
        def _index_value(key):
            if bool(specialized_properties):
                for indx in specialized_properties:
                    if indx['key'] == key:
                        return indx['value']
            return None
        
        var = super(product_spt, self).FromTTRxToOdoo(values)

        description = {}
        if bool(values.get('descriptions')):
            description.update(values['descriptions'][0])

        specialized_properties = values.get('specialized_properties')
        
        dosage_form_id = self.env['pharma.dosage.forms.spt'].search([('code','=',_index_value('dosage_form'))],limit=1).id or None
        state_id = values.get('status') and self.env['products.status.spt'].search([('value','=',values['status'])],limit=1).id or None
        product_type_id = values.get('type_class') and self.env['products.types.spt'].search([('value','=',values['type_class'])],limit=1).id or None

        var.update({
            'uuid': values.get('uuid'),
            'created_on': DateTimeToOdoo(values.get('created_on')),
            'last_update': DateTimeToOdoo(values.get('last_update')),
            'name': description['name'] if bool(description) else None,
            'type': 'product' if not bool(values) else None,
            'tracking': 'serial' if not bool(values) else None,
            'description': description['description'] if bool(description) else None,
            'composition': description['composition'] if bool(description) else None,
            'long_name': description['product_long_name'] if bool(description) else None,
            'gs1_company_prefix': values.get('gs1_company_prefix'),
            'gs1_id': values.get('gs1_id'),
            'barcode': values.get('upc') if bool(values.get('upc')) else False,
            'default_code': values.get('sku'),
            'categ_id': None,
            'state_id': state_id,
            'product_type_id': product_type_id,
            'manufacturer_id': None,
            'description_ids': None,
            'packaging_ids': None,
            'product_identifiers': None,
            'requirement_ids': None,
            'composition_ids': None,
            'strength': _index_value('strength'),
            'dosage_form_id': dosage_form_id,
            'generic_name': _index_value('generic_name'),
            'us_size': _index_value('us_size'),
            'gender': _index_value('gender'),
            'pack_size': values.get('pack_size'),
            'pack_size_type_id': None,
            'description_purchase': values.get('notes'),
            'active': values.get('is_active'),
            'is_leaf_product': values.get('is_leaf_product'),
            'gtin14': values.get('gtin14'),
        })
        CleanDataDict(var)
        return var

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
    
            if bool(response.get('identifiers')):
                ttr_ident_ids = [x['id'] for x in response['identifiers']] if bool(response.get('identifiers')) else []
                ident_ids = []
                for ttr_ident_id in ttr_ident_ids: 
                    ident_ids += self.env['product.identifier.spt'].SyncFromTTRx(connector,product_uuid=self.uuid,
                                                                                identifier_id=ttr_ident_id,
                                                                                update=False).ids
                self.with_context(context).identifier_ids = [(6,0, ident_ids)] if bool(ident_ids) else [(5,)]
    
            if bool(response.get('composition')):
                comp_ids = []
                for composition in response['composition']:
                    comp_ids += self.env['product.composition.spt'].SyncFromTTRx(connector,product_uuid=self.uuid,
                                                                                 child_product_uuid=composition['product_uuid'],
                                                                                 update=False).ids
                self.with_context(context).composition_ids = [(6,0, comp_ids)] if bool(comp_ids) else [(5,)]

        return True

    def action_send(self):
        for reg in self:
            reg.CreateInTTRx()
        return True

    def action_refresh(self):
        for reg in self:
            reg.SyncFromTTRx(self.connector_id,myown=True)
        return True

    def action_test(self):
        self.env['product.description.spt'].TTRxSearch(self.connector_id,product_uuid='6fd1dd3b-e629-41ab-8858-5c3c881a112e',
                                                       description_language_code="en")

