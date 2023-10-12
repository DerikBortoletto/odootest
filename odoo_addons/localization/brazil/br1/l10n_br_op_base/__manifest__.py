{
    'name': 'Módulo Base - Brasil',
    'description': 'TrackErp Brazilian Localization Base',
    'version': '14.0.0.1',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'TrackErp Brasil',
    'website': 'http://www.trackerp.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'depends': [
        'base', 
        'web',
    ],
    'data': [
        # Views
        'views/br_base.xml',
        'views/ir_module.xml',
        'views/br_base_view.xml',
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
        'views/res_bank_view.xml',
        'views/res_partner_bank_view.xml',
        'views/res_company_view.xml',
        'views/base_assets.xml',
        # Security
        'security/ir.model.access.csv',
    ],
    'installable': True,
    "pre_init_hook": "pre_init_hook",
    # "post_init_hook": "post_init_hook",
    "development_status": "Mature",
}
