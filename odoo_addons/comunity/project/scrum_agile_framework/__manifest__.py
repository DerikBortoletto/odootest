# -*- coding: utf-8 -*-
{
    'name': "Scrum Project Framework",

    'summary': """
        Framework for managing Scrum Team projects""",

    'description': """
        This framework allows us to unify all the aspects in the agile methodologies work environment
        The objective is to relate the existing modules (Projects, Timesheets and Employees) in order to have a complete application..
        The icon comes from https://www.flaticon.es/iconos-gratis/mele"
    """,

    'author': "Iñigo Idoate Sagardia",
    'website': "https://github.com/idoate/OdooApps/tree/14.0",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Services/Project',
    'version': '14.0.2.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base_setup',
        'project',
        'hr',
        'analytic',
        'mail',
        'portal',
        'rating',
        'resource',
        'web',
        'web_tour',
        'digest',
    ],

    # always loaded
    'data': [
        'security/scrum_security.xml',
        'security/ir.model.access.csv',
        'views/user_story_view.xml',
        'views/sprint_view.xml',
        'views/team_view.xml',
        'views/meeting_view.xml',
        'views/task_view.xml',
        'views/project_view.xml',
        'views/burndown_view.xml',
        'views/menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    # Indicamos que es una aplicacion
    'application': True,
}
