{
    'name': 'Odoo Hubspot Integration',
    'version': '14.0.18',
    'category': 'Hubspot',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': 'pragtech.co.in',
    'summary': 'Integration of Odoo Partners with hubspot contacts Odoo Hubspot Integration App odoo hubspot odoo Hubspot connector odoo Hubspot integration hubspot crm',
    'description': """
Hubspot Integration
==========================
Odoo Partners are imported and updated from and to Hubspot.
Using Hubspot API data is synced.
<keywords>
Odoo Hubspot Integration App
Hubspot
odoo hubspot
odoo Hubspot connector
odoo Hubspot integration
hubspot crm
    """,
    'depends': ['base', 'base_setup', 'sale_management', 'crm', 'helpdesk'],
    'external_dependencies': {
        'python': ['pyrecord', 'builtins'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'data/tag_data.xml',
        'views/res_partner_view.xml',
        'views/hubspot_scheduler.xml',
        'views/hubspot_instance_view.xml',
        'views/hubspot_logger_view.xml',
        'views/res_users_view.xml',
        'views/mail_activity_view.xml',
        'views/mail_message_view.xml',
        'views/crm_lead_view.xml',
        'wizards/message_view.xml',
        'views/calendar_event_view.xml',
        'views/hubspot_contact_fields.xml',
        'views/hubspot_company_fields.xml',
        'views/hubspot_deals_fields.xml',
        'views/hubspot_tickets_fields.xml',
        'views/ticket_view.xml',
    ],
    'images': ['images/New-Hubspot-Gif-Animation.gif'],
    # 'images': ['static/description/end-of-year-sale-main.jpg'],
    # 'images': ['static/description/end_of_year_sale.gif'],
    'live_test_url': 'http://www.pragtech.co.in/company/proposal-form.html?id=103&name=hubspot',
    'price': 199.00,
    'currency': 'USD',
    'license': 'OPL-1',
    'application': True,
    'auto_install': False,
    'installable': True,
}
