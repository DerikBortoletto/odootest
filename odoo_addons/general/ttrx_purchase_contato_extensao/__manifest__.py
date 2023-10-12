# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase Extensao',
    'version': '1.2',
    'category': 'Inventory/Purchase',
    'sequence': 35,
    'summary': 'Purchase orders, tenders and agreements',
    'description': "",
    'website': 'https://www.odoo.com/page/purchase',
    'depends': ['account', 'purchase'],
    'data': [
        'views/purchase_views.xml',
    ],
    'qweb': [
    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
