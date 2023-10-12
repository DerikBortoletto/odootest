# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Módulo Base Core - Brasil",
    "summary": "Customization of base module for implementations in Brazil.",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "TrackErp Brasil",
    "maintainers": ["Defendi"],
    "website": "http://www.trackerp.com",
    "version": "14.0.3.0.3",
    "depends": ["base", "base_setup", "base_address_city", "base_address_extended", "l10n_br"],
    "data": [
        "security/ir.model.access.csv",
        "data/res.city.csv",
        "data/res.country.state.csv",
        "data/res.bank.csv",
        "views/webclient_templates.xml",
        "views/res_partner_address_view.xml",
        "views/res_config_settings_view.xml",
        "data/res_country_data.xml",
        "views/res_city_view.xml",
        "views/res_bank_view.xml",
        "views/res_partner_bank_view.xml",
        "views/res_country_view.xml",
        "views/res_partner_view.xml",
        "views/res_company_view.xml",
    ],
    "demo": [
        "demo/l10n_br_base_demo.xml",
        "demo/res_partner_demo.xml",
        "demo/res_company_demo.xml",
        "demo/res_users_demo.xml",
        "demo/res_partner_pix_demo.xml",
    ],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
    "development_status": "Mature",
    "external_dependencies": {
        "python": ["num2words", "erpbrasil.base", "phonenumbers", "email_validator"]
    },
}
