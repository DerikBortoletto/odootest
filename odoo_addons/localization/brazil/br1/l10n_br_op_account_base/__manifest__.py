{
    'name': 'Módulo Base Contas - Brasil',
    'description': 'TrackErp BR Localization account Base',
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
            'pytrustnfe.nfe', 'pytrustnfe.certificado'
        ],
    },
    'depends': [
        'product',
        'account',
        'l10n_br_op_base_fiscal', 
    ],
    'data': [
        'views/base_fiscal_view.xml',
        'views/product_view.xml',
        'views/account_account_view.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/res_config_settings_views.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
    ],
    'installable': True,
}
