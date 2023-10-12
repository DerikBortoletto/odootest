
from odoo import models, fields, api
from odoo.exceptions import UserError

ITEMCLASS = [
    ('rx','RX'),
    ('otc', 'OTC')
]

CTRLSUBS = [
    ('c1', 'C1'),
    ('c2', 'C2'),
    ('c3', 'C3'),
]

STORTEMP = [
    ('1', '2 to 8 degrees Celsius'),
    ('2', 'below 0 degrees Celsius'),
]

SIZE = [
    ('ml', 'Ml'),
    ('tabs', 'Tabs'),
    ('caps', 'Caps')
]

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    barcode = fields.Char('NDC UPC', compute='_compute_barcode', inverse='_set_barcode', search='_search_barcode')
    default_code = fields.Char('SKU', compute='_compute_default_code', inverse='_set_default_code', store=True)
    standard_price = fields.Float('Cost Price', compute='_compute_standard_price', inverse='_set_standard_price', search='_search_standard_price',
                                  digits='Product Price', groups="base.group_user", help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
                                                                                            In FIFO: value of the next unit that will leave the stock (automatically computed).
                                                                                            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
                                                                                            Used to compute margins on sale orders.""")
    
    generic_name = fields.Char(string="Generic Name")
    manufacture_id = fields.Many2one('res.partner', string='Manufacture')
    item_class = fields.Selection(ITEMCLASS,string="Class")
    control_substance = fields.Boolean('Control Substance', default=False)
    control_substance_type = fields.Selection(CTRLSUBS,string="Control Type")
    storage_temperature = fields.Selection(STORTEMP,string="Temperature")
    size = fields.Selection(SIZE,string="Size")
    pharm_description = fields.Char('Pharm Description', compute="_compute_pharm_description", store=False, readonly=True)
    
    @api.depends('generic_name', 'product_brand_id', 'manufacture_id', 'item_class', 
                 'control_substance', 'control_substance_type', 'storage_temperature')
    def _compute_pharm_description(self):
        for prod in self:
            desc = []
            if bool(prod.generic_name):
                desc.append(str(prod.generic_name))
            if bool(prod.product_brand_id):
                desc.append('Brand %s' % str(prod.product_brand_id.name or prod.description))
            if bool(prod.manufacture_id):
                desc.append('Manufacture %s' % str(prod.manufacture_id.name))
            if bool(prod.item_class):
                desc.append('Class %s' % str(dict(prod._fields['item_class'].selection).get(prod.item_class)))
            if prod.control_substance and bool(prod.control_substance_type):
                desc.append('Control Subs. %s' % str(dict(prod._fields['control_substance_type'].selection).get(prod.control_substance_type)))
            if bool(prod.storage_temperature):
                desc.append('Temp. %s' % str(dict(prod._fields['storage_temperature'].selection).get(prod.storage_temperature)))
            prod.pharm_description = str(', '.join(desc)).capitalize()

class ProductProduct(models.Model):
    _inherit = "product.product"

    default_code = fields.Char('SKU', index=True)
    barcode = fields.Char('NDC UPC', copy=False, help="International Article Number used for product identification.")
    standard_price = fields.Float('Cost Price', company_dependent=True, digits='Product Price', groups="base.group_user", 
                                  help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
                                          In FIFO: value of the next unit that will leave the stock (automatically computed).
                                          Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
                                          Used to compute margins on sale orders.""")


    def get_product_multiline_description_sale(self):
        self.ensure_one()
        super(ProductProduct, self).get_product_multiline_description_sale()
        name = self.name
        if self.pharm_description:
            if self.generic_name:
                name = self.pharm_description
            else:
                name += ' ' + self.pharm_description
        if self.description_sale:
            name += '\n' + self.description_sale

        return name
