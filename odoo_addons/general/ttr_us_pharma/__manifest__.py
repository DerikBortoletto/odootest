{
    'name': 'TTRX Module USA Pharma Product - General',
    'description': 'TTRx General Pharma Product Module for USA',
    'version': '14.0.0.1',
    'category': 'Inventory',
    'license': 'AGPL-3',
    'author': 'TTRx Brasil',
    'website': 'http://tracktracerx.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'depends': [
        'uom',
        'product',
        'product_brand',
        'stock',
        'account',
        'purchase',
        'sale',
    ],
    'data': [
        # 'views/uom_uom_view.xml',
        'views/invoice_view.xml',
        'views/product_view.xml',
        'views/purchase_order_view.xml',
        'views/sale_order_view.xml',
        'views/picking_view.xml',
        # 'views/report_invoice.xml'
        # 'security/ir.model.access.csv',
    ],
    'installable': True,
    # 'auto_install': True,
}
