import logging
import re

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.addons.l10n_br_op_base.tools import fiscal
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

# Subset of partner fields: sync any of those
PARTNER_FIELDS_TO_SYNC = [
    'mobile',
    'title',
    'function',
    'website',
    'legal_name',
    'inscr_est',
    'inscr_mun',
    'suframa',
    'rntrc',
]

# Subset of partner fields: sync all or none to avoid mixed addresses
PARTNER_ADDRESS_FIELDS_TO_SYNC = [
    'street',
    'number',
    'street2',
    'district',
    'city',
    'zip',
    'city_id',
    'state_id',
    'country_id',
]

class Lead(models.Model):
    _inherit = "crm.lead"

    legal_name = fields.Char('Legal Name', size=60, help="Name used in fiscal documents")
    cnpj = fields.Char('CNPJ', size=18, copy=False)
    cpf = fields.Char('CPF', size=14, copy=False)
    rg = fields.Char('RG', size=16)
    inscr_est = fields.Char('State Inscription', size=16, copy=False, help='Em pessoas jurídicas sem o I.E. utilise a palavra "ISENTO"')
    inscr_mun = fields.Char('Municipal Inscription', size=18)
    city_id = fields.Many2one('res.state.city', 'City', domain="[('state_id','=',state_id)]")
    district = fields.Char('District', size=32)
    number = fields.Char('Number', size=10)
    suframa = fields.Char('Suframa', size=18)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    ibge_code = fields.Char(related='country_id.ibge_code')
    city_name = fields.Char(related="city_id.name")
    rntrc = fields.Char(string='RNTRC', size=10, help="Registro Nacional de Transportadores Rodoviários de Carga")

    @api.constrains('cnpj')
    def _check_cnpj(self):
        for item in self:
            if item.cnpj:
                if not fiscal.validate_cnpj(item.cnpj):
                    raise ValidationError(_('CNPJ inválido!'))
        return True

    @api.constrains('cpf')
    def _check_cpf(self):
        for item in self:
            if item.cpf:
                if not fiscal.validate_cpf(item.cpf):
                    raise ValidationError(_('CPF inválido!'))
        return True

    @api.onchange('cnpj')
    def onchange_mask_cnpj(self):
        if self.cnpj:
            val = re.sub('[^0-9]', '', self.cnpj)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                self.cnpj = cnpj_cpf
            else:
                raise UserError(_('Verifique o CNPJ'))

    @api.onchange('cpf')
    def onchange_mask_cpf(self):
        if self.cpf:
            val = re.sub('[^0-9]', '', self.cpf)
            if len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                    % (val[0:3], val[3:6], val[6:9], val[9:11])
                self.cpf = cnpj_cpf
            else:
                raise UserError(_('Verifique o CPF'))

    @api.onchange('city_id')
    def onchange_city_id(self):
        if self.city_id:
            self.city = self.city_id.name

    def _validate_ie_param(self, uf, inscr_est):
        try:
            mod = __import__('odoo.addons.l10n_br_op_base.tools', globals(), locals(), 'fiscal')
            validate = getattr(mod, 'validate_ie_%s' % uf)
            if not validate(inscr_est):
                return False
        except AttributeError:
            if not fiscal.validate_ie_param(uf, inscr_est):
                return False
        return True

    @api.constrains('inscr_est')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False."""
        if not self.inscr_est or self.inscr_est == 'ISENTO':
            return True
        uf = self.state_id and self.state_id.code.lower() or ''
        res = self._validate_ie_param(uf, self.inscr_est)
        if not res:
            raise ValidationError(_(u'Inscrição Estadual inválida!'))
        return True

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        result = super(Lead, self)._prepare_values_from_partner(self.partner_id)

        if self.partner_id:
            result["street"] = self.partner_id.street
            result["number"] = self.partner_id.number
            result["street2"] = self.partner_id.street2
            result["district"] = self.partner_id.district
            result["city_id"] = self.partner_id.city_id.id
            result["country_id"] = self.partner_id.country_id.id
            if self.partner_id.is_company:
                result["legal_name"] = self.partner_id.legal_name
                result["cnpj"] = self.partner_id.cnpj_cpf
                result["inscr_est"] = self.partner_id.inscr_est
                result["inscr_mun"] = self.partner_id.inscr_mun
                result["suframa"] = self.partner_id.suframa
            else:
                result["partner_name"] = self.partner_id.parent_id.name or False
                result["legal_name"] = self.partner_id.parent_id.legal_name or False
                result["cnpj"] = self.partner_id.parent_id.cnpj_cpf or False
                result["inscr_est"] = self.partner_id.parent_id.inscr_est or False
                result["inscr_mun"] = self.partner_id.parent_id.inscr_mun or False
                result["suframa"] = self.partner_id.parent_id.suframa or False
                result["website"] = self.partner_id.parent_id.website or False
                result["cpf"] = self.partner_id.cnpj_cpf
                result["rg"] = self.partner_id.rg_fisica
                result["contact_name"] = self.partner_id.legal_name
        self.update(result)
        return result

    def _prepare_address_values_from_partner(self, partner):
        # Sync all address fields from partner, or none, to avoid mixing them.
        vals = super()._prepare_address_values_from_partner(partner)
        vals.update({f: self[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC})
        vals.update({f: partner[f] or self[f] for f in PARTNER_FIELDS_TO_SYNC})
        return vals
    
    def _prepare_values_from_partner(self, partner):
        vals = super()._prepare_values_from_partner(partner)
        vals.update({f: partner[f] or self[f] for f in PARTNER_FIELDS_TO_SYNC})
        return self._convert_to_write(vals)
    
    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        """ Extract data from lead to create a partner.

        :param name : furtur name of the partner
        :param is_company : True if the partner is a company
        :param parent_id : id of the parent partner (False if no parent)

        :return: dictionary of values to give at res_partner.create()
        """
        email_split = tools.email_split(self.email_from)
        ind_ie = '9' if not is_company or not bool(self.inscr_est) else '2' if self.inscr_est == 'ISENTO' else '1'
        res = {
            'name': partner_name,
            'legal_name': self.legal_name,
            'cnpj_cpf': self.cnpj if is_company else self.cpf,
            'rg_fisica': self.rg if not is_company else False,
            'inscr_est': self.inscr_est if is_company else False,
            'indicador_ie_dest': ind_ie,
            'inscr_mun': self.inscr_mun,
            'suframa': self.suframa,
            'rntrc': self.rntrc,
            'user_id': self.env.context.get('default_user_id') or self.user_id.id,
            'comment': self.description,
            'team_id': self.team_id.id,
            'parent_id': parent_id,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': email_split[0] if email_split else False,
            'title': self.title.id,
            'function': self.function,
            'street': self.street,
            'number': self.number,
            'street2': self.street2,
            'district': self.district,
            'zip': self.zip,
            'city': self.city,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'city_id': self.city_id.id,
            'website': self.website,
            'is_company': is_company,
            'carrier': True if bool(self.rntrc) else False,
            'type': 'contact'
        }
        if self.lang_id:
            res['lang'] = self.lang_id.code
        return res

