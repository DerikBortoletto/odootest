{
    'name': 'New Licenses Control',
    'category': 'services',
    'summary': 'Ornaganize your Licences',
    'license': 'LGPL-3',
    'version': '14.0.0.1',
    'description': """""
"
This module provides a quick overview of your License Control directory, accessible from your home page.
You can track your licenses, expiry dates and values.
""",
    'depends': [
        'base',
        'sale',
        'product',
        'ttrx2_connector_spt',

    ],
    'data': [
            'views/licenses_ctrl_views.xml',
            'views/licenses_types_views.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,


}