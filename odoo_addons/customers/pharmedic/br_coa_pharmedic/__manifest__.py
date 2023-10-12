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
        'account', 
    ],
    'data': [
        'data/account.group.csv',
        'data/short_code_sequence.xml',
        'data/br_chart_data.xml',
        'data/account.account.template.csv',
        'data/account_template_data.xml',
        'data/product_account.xml',
    ],
    'active': True,
}
