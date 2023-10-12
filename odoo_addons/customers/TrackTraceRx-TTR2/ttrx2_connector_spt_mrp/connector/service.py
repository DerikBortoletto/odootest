
# Methods
METHOD_POST = 'POST'
METHOD_GET = 'GET'
METHOD_PUT = 'PUT'
METHOD_DELETE = 'DELETE'
METHOD_LIST = 'LIST'

METHODS = [METHOD_GET, METHOD_LIST, METHOD_POST, METHOD_PUT, METHOD_DELETE]

URI = {
    'identifiers_types': 'products/identifiers_types',
    'res.partner': 'trading_partners/{uuid}',
    'license.spt.partner': 'trading_partners/{partner_uuid}/licences/{id}',
    'license.spt.location': 'locations/{location_uuid}/licences/{id}',
    'license.spt.address': 'address_book/{address_uuid}/licences/{id}',
    'license.types.management.spt': 'company_management/licences_type/{id}',
    'license.attachments.spt.partner': 'trading_partners/{partner_uuid}/licences/{licence_id}/attachments{attachment_id}',
    'license.attachments.spt.location': 'location/{location_uuid}/licences/{licence_id}/attachments{attachment_id}',
    'license.attachments.spt.address': 'addresss_book/{address_uuid}/licences/{licence_id}/attachments{attachment_id}',
    'trading.partner.address.spt.partner': 'trading_partners/{partner_uuid}/addresses/{uuid}',
    'trading.partner.address.spt.location': 'locations/{location_uuid}/addresses/{uuid}',
    'trading.partner.address.spt.manufacturer': 'company_management/manufacturer/{manufacturer_id}/addresses/{uuid}',
    'trading.partner.users.spt': 'trading_partners/{partner_uuid}/users/{uuid}',
    'pharma.dosage.forms.spt': 'products/pharmaceutical/dosage_forms/{id}',
    'product.spt': 'products/{uuid}',
    'product.category': 'company_management/product_categories/{id}',
    'product.requirement.spt': 'company_management/product_requirements/{product_require_id}',
    'product.requirement.spt.categories': 'company_management/product_categories/{category_id}/requirements/{id}',
    'pro.require.conditions.spt': 'company_management/product_requirements/{prod_req_id}/conditions/{id}',
    'product.description.spt': 'products/{product_uuid}/description/{description_language_code}',
    'product.identifier.spt': 'products/{product_uuid}/identifiers/{id}',
    'identifiers.types.spt': 'products/identifiers_types',
    'products.status.spt': 'products/status_list',
    'product.composition.spt': 'products/{product_uuid}/composition/{child_product_uuid}',
    'product.packaging.spt': 'products/{product_uuid}/packaging/{uuid}',
    'product.packaging.layers.spt': 'products/{product_uuid}/packaging/{packaging_uuid}/layers/{id}',
    'pack.size.type.spt': 'products/packaging_types/{packing_type_id}',
    'products.types.spt': 'products/types',
    'locations.management.spt': 'locations/{uuid}',
    'storage.areas.spt': 'locations/{location_uuid}/storage_areas/{uuid}',
    'shelf.spt': 'locations/{location_uuid}/storage_areas/{storage_uuid}/storage_shelfs/{storage_shelf_uuid}',
    'read.points.spt': 'locations/{location_uuid}/readpoints/{readpoint_uuid}',
    'thrid.party.logistic.provide.spt': 'company_management/third_party_management/{uuid}',
    'manufacturers.spt': 'company_management/manufacturer/{id}',
    'container.spt.list': 'containers_search',
    'container.spt.post': 'containers',
    'container.spt': 'containers/{container_id_type}/{container_identifier}',
    'disposition.spt': 'company_management/dispositions',
    'business.step.spt': 'company_management/business_steps',
    'product.lot.spt': 'products/{product_uuid}/lot',
    'purchase.order': 'transactions/purchase/{uuid}',
    'sale.order': 'transactions/sales/{uuid}',
    'stock.picking.outgoing': 'shipments/Outbound',
    'stock.picking.incoming': 'shipments/Inbound',
    'picking.spt': 'shipments/picking/{uuid}',
    'picking.spt.pick_close': 'shipments/picking/{shipment_picking_uuid}/pick_and_close',
}

def uri_exist(resource):
    res = True
    try:
        bool(URI[resource])
    except:
        res = False
    return res

def get_uri(resource,method=METHOD_LIST):
    try:
        complemento = URI[resource]
        if method in [METHOD_LIST,METHOD_POST]:
            if complemento[-1] == '}':
                apos = complemento.rindex('{')
                complemento = complemento[:apos]
            if complemento[-1] == '/':
                complemento = complemento[:len(complemento)-1] 
    except:
        return ''
    
    return "/%s" % (complemento)

def get_uri_list(resource):
    try:
        complemento = URI[resource]
    except:
        return ''
    
    return "/%s" % (complemento)

def get_list_param(resource):
    uri = get_uri(resource, 'GET')
    res = []
    if bool(uri):
        a = uri.find('{')
        while a > 0:
            b = uri.find('}')
            if b > a:
                val = uri[a+1:b]
                if len(val) > 0:
                    res.append(val)
                uri = uri[:a-1]+uri[b+1:]
                a = uri.find('{')
    return res
    
def get_last_param(resource,default=None):
    uri = get_uri(resource, 'GET')
    x1 = str(uri).rfind('{')
    x2 = str(uri).rfind('}')
    if x1 >= 0 and x2 > x1:
        return uri[x1+1:x2]
    else:
        return default

def get_total_param(resource):
    return len(get_list_param(resource))
    