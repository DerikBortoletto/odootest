{
    'name': 'TrackErp Módulo Base Fiscal - Brasil',
    'description': 'TrackErp Brazilian Localization Fiscal Base',
    'version': '14.0.0.1',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'TrackErp Brasil',
    'website': 'http://www.trackerp.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'depends': [
        'l10n_br_op_base',
    ],
    'data': [
         'views/res_company_view.xml',
         'views/res_partner_view.xml',
    ],
    'installable': True,
}
