{
    'name': 'TTRx Módulo Account - Due Date in Invoices',
    'description': 'TTRx General Account payment',
    'version': '14.0.0.1',
    'category': 'Account',
    'license': 'AGPL-3',
    'author': 'TTRx Brasil',
    'website': 'http://www.tracktracerx.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'depends': [
        'ttr_account_extra',
    ],
    'data': [
        'views/account_move_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    # 'auto_install': True,
}
