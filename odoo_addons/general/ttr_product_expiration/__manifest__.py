{
    'name': 'TTR Módulo Expiration Stock',
    'description': 'Track Erp ',
    'version': '14.0.0.1',
    'category': 'Inventory',
    'license': 'AGPL-3',
    'author': 'Tracktrace International',
    'website': 'https://www.tracktracerx.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'depends': [
        'product_expiry',
    ],
    'data': [
        # 'views/product_view.xml',
        # 'views/stock_move_view.xml',
        'views/stock_production_lot_view.xml',
    ],
    'installable': True,
    # 'auto_install': True,
}
