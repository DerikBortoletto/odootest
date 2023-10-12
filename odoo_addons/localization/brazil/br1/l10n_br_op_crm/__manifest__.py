{
    'name': 'Módulo CRM - Brasil',
    'description': 'TrackErp Brazilian Localization CRM',
    'version': '14.0.0.1',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'TrackErp Brasil',
    'website': 'http://www.trackerp.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'depends': [
        'crm',
        'l10n_br_op_base_fiscal', 
    ],
    'data': [
        'views/crm_lead_view.xml',
        'views/crm_quick_create_opportunity_form.xml',
    ],
    'test': [
    ],
    # 'qweb': ['static/src/xml/*.xml'],
    # 'post_init_hook': 'post_init',
    'installable': True,
    # 'auto_install': True,
}
