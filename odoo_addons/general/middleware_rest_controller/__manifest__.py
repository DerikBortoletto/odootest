# -*- coding: utf-8 -*-
{
    "name": "Middleware REST Controller",
    "summary": """
        Middleware REST Controller
    """,
    "description": """
        Middleware REST Controller, a gateway to communicate with the middleware
    """,
    "author": "Dhiman Sarkar",
    "website": "https://www.aqbsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list

    "category": "API",
    "version": "1.0",

    # any module necessary for this one to work correctly
    "depends": ["sale_management", "account", "stock", "purchase", "base"],

    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/default.xml",
        "wizard/middleware_confirm_wizard_view.xml"
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
    "license": "LGPL-3",
}
