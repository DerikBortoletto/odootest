{
    'name': 'TTRX Módulo Product - General',
    'description': 'TTRx General Product Module',
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
        'account',
    ],
    'data': [
        'views/uom_uom_view.xml',
        'views/product_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    # 'auto_install': True,
}
