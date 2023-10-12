# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Módulo Account NFe/NFC-e Integration - Brasil",
    "summary": "Integration between l10n_br_account and l10n_br_nfe",
    "category": "Localisation",
    "author": "TrackErp Brasil",
    "maintainers": ["Defendi"],
    "website": "http://www.trackerp.com",
    "version": "14.0.1.2.2",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_nfe",
        "l10n_br_account",
        "account_payment_partner",
    ],
    "data": [
        "views/account_payment_mode.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": True,
}
