# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Stock Picking Invoice Link",
    "version": "14.0.1.1.1",
    "category": "Warehouse Management",
    "summary": "Adds link between pickings and invoices",
    "author": "Agile Business Group, "
    "Tecnativa, "
    "BCIM sprl, "
    "Softdil S.L, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-workflow",
    "license": "AGPL-3",
    "depends": ["sale_stock"],
    "data": [
        "views/stock_view.xml", 
        "views/account_invoice_view.xml"
    ],
    "installable": True,
    "post_init_hook": "post_init",
}
