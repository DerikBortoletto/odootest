{
    'name': 'Módulo Base Estoque - Brasil',
    'description': 'TrackErp Brazilian Localization Stock Base',
    'version': '14.0.0.1',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'TrackErp Brasil',
    'website': 'http://www.trackerp.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'depends': [
        'stock',
        'l10n_br_op_base_fiscal', 
    ],
    'data': [
        'views/product_view.xml',
    ],
    'installable': True,
}
