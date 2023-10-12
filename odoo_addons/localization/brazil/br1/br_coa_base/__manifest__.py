{  
    'name': 'TrackErp Plano de Contas Base',
    'summary': """Trackerp Plano de contas base""",
    'description': """Trackerp Plano de contas Brasileiro""",
    'version': '14.0.0.1',
    'category': 'Localization',
    'author': 'Trackerp',
    'license': 'AGPL-3',
    'website': 'http://www.trackerp.com',
    'contributors': [
        'Alexandre Defendi <alexandre@trackerp.com>',
    ],
    'depends': [
        'account', 'l10n_br_op_account_data',
    ],
    'data': [
        'data/account.group.csv',
        'data/br_chart_data.xml',
        'data/account.account.template.csv',
        'data/account_tax_template_data.xml',
    ],
    'active': True,
}
