{
    'name': 'Professional BI Extension',
    'version': '14.0.0.1',
    'summary': 'Professional BI',
    'author': 'André Leopoldino', 'Vinicius Melo'
    'sequence': 1,
    'license': 'AGPL-3',
    'website': 'https://www.tracktracerx.com',
    'category': 'Services',
    'description': "",
    'depends': [
        'bi_professional_reports_templates',
        'base',
        'contacts',
    ],
    'data': [
        #Views
        'views/sale_order.xml'

        

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
