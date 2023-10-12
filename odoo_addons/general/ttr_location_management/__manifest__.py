{
    'name': 'TTRx Módulo location - Management',
    'description': 'TTRx Location Management',
    'version': '14.0.0.1',
    'category': 'Inventory',
    'license': 'AGPL-3',
    'author': 'TTRx Brasil',
    'website': 'http://www.tracktracerx.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'depends': [
        'base', 
        'web',
        'stock',
    ],
    'data': [
        'views/stock_location_view.xml',
    ],
    'installable': True,
    # 'auto_install': True,
}
