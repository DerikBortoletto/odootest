# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Helpdesk Timesheet',
    'category': 'Services/Helpdesk',
    'summary': 'Project, Tasks, Timesheet',
    'depends': ['project', 'hr_timesheet', 'helpdesk'],
    'description': """
        - Allow to set project for Helpdesk team
        - Track timesheet for a task from a ticket
    """,
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/helpdesk_timesheet_security.xml',
        'views/helpdesk_views.xml',
        # 'views/project_views.xml',
        # 'wizard/helpdesk_ticket_create_timesheet_views.xml',
        # 'data/helpdesk_timesheet_data.xml',
    ],
    'demo': ['data/helpdesk_timesheet_demo.xml'],
    'license': 'LGPL-3',
    'post_init_hook': '_helpdesk_timesheet_post_init'
}
