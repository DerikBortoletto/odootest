{
    'name': 'TTRx Módulo ZIFT Invoice - Management',
    'description': 'TTRx Location Management',
    'version': '14.0.0.1',
    'category': 'Inventory',
    'license': 'AGPL-3',
    'author': 'TTRx Brasil',
    'website': 'http://www.tracktracerx.com',
    'contributors': [
    ],
    'depends': [
        'base', 
        'web',
        'stock',
    ],
    'data': [
        'views/stock_location_view.xml',
        'views/location_line.xml',
        'security/ir.model.access.csv',
        'views/automatic.xml'
    ],
    'installable': True,
    # 'auto_install': True,
}
