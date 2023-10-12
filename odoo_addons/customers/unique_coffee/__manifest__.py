{
    'name': 'Unique Coffee',
    'version': '14.0.0.1',
    'summary': 'Unique Coffee administration module',
    'author': 'Johnatan Souza TTRX',
    'sequence': 1,
    'license': 'AGPL-3',
    'website': 'https://www.tracktracerx.com',
    'category': 'Services',
    'description': "",
    'depends': [
        'website',
        'base',
        'contacts',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Views
        "views/unique_contacts_form_view.xml",
        "views/unique_success.xml",
        "views/unique_contacts_menu.xml",
        "views/unique_contacts_form.xml",

    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'css': [
        'static/src/css/style.css',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
