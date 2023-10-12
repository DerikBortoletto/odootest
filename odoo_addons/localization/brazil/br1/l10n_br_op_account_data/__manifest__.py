{
    'name': 'Módulo Dados Base do Fiscal - Brasil',
    'description': 'TrackErp Brazilian Localization Data account Base',
    'version': '14.0.0.1',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'TrackErp Brasil',
    'website': 'http://www.trackerp.com',
    'contributors': [
        'Alexandre Defendi <alexandre@tracktracerx.com>',
    ],
    'depends': [
        'l10n_br_op_account_base', 
    ],
    'data': [
        'data/br.beneficio.fiscal.csv',
        'data/br.cfop.csv',
        'data/br.cnae.csv',
        'data/br.enquadramento.ipi.csv',
        'data/br.ncm.csv',
        'data/br.service.type.csv',
    ],
    'test': [
        # 'test/base_inscr_est_valid.yml',
        # 'test/base_inscr_est_invalid.yml',
    ],
    # 'qweb': ['static/src/xml/*.xml'],
    # 'post_init_hook': 'post_init',
    'installable': True,
    # 'auto_install': True,
}
