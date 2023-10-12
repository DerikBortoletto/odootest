{
    'name': 'Tecnospeed NFe Integration',
    'version': '14.0.0.1',
    'summary': 'NFe integration with tecnospeed API provider',
    'author': ['André Leopoldino','Vinicius Melo', 'Johnatan Souza'],
    'sequence': 1,
    'license': 'AGPL-3',
    'website': 'https://www.tracktracerx.com',
    'category': 'Services',
    'description': "",
    'depends': [
        'purchase',
        'contacts',
        'sale',
        'account',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Views
        "views/purchase_order.xml",
        "views/purchase_order_tree.xml",
        "views/tributos.xml",
        "views/product_template.xml",
        "views/stock_picking.xml",
        "views/stock_production_lot.xml",
        "views/sale_order_tree.xml",
        "views/sale_tributos.xml",
        "views/res_company.xml",
        "views/res_partner.xml"
      

        

    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
