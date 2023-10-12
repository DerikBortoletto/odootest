# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Módulo Account Payment BRCobranca - Brasil",
    "version": "14.0.3.0.1",
    "license": "AGPL-3",
    "author": "TrackErp Brasil",
    "maintainers": ["Defendi"],
    "website": "http://www.trackerp.com",
    "depends": [
        "l10n_br_account_payment_order",
        "account_move_base_import",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/account_move_view.xml",
        "views/account_journal_view.xml",
        # Wizard
        "wizard/import_statement_view.xml",
    ],
    "demo": [
        "demo/account_journal_demo.xml",
        "demo/account_move_demo.xml",
        "demo/account_payment_mode.xml",
    ],
}
