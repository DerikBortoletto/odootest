# -*- coding: utf-8 -*-

{
    'name': 'Zift Payment Acquirer',
    'category': 'Accounting/Payment Acquirers',
    'sequence': 350,
    'summary': 'Payment Acquirer: Zift Implementation',
    'version': '1.0',
    'description': """Zift Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_zift_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'application': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
