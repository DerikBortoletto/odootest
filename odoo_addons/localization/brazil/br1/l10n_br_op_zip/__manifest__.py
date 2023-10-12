{  
    'name': 'Módulo ZIP - Brasil',
    'description': 'TrackErp Brazilian Localization ZIP Codes Brasil',
    'version': '14.0.0.1',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'TrackErp Brasil',
    'website': 'http://www.trackerp.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'external_dependencies': {
        'python': [
            'zeep',
        ],
    },
    'depends': [
        'l10n_br_op_base',
    ],
    'data': [
        'views/br_zip_view.xml',
        'views/res_partner_view.xml',
        'views/res_bank_view.xml',
        'wizard/br_zip_search_view.xml',
        'security/ir.model.access.csv',
    ],
    # 'test': ['test/zip_demo.yml'],
    'installable': True,
}
