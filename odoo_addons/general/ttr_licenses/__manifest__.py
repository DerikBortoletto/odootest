# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Licenses Control',
    'category': 'services',
    'summary': 'Centralize your Licences',
    'description': """""
"
This module provides a quick overview of your License Control directory, accessible from your home page.
You can track your licenses, expiry dates and values.
""",
    'depends': ['base','sale','product'],
    'data': [
            'views/licenses_control_views.xml',
            'views/licenses_types_views.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
