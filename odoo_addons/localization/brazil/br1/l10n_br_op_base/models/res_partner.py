
import re
import base64
import logging

from odoo import models, fields, api, _
from ..tools import fiscal
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _rec_name = 'display_name'
    
    def _default_country(self):
        return self.env['res.country'].search([('ibge_code', '=', '1058')],limit=1).id

    cnpj_cpf = fields.Char('CNPJ/CPF', size=18, copy=False)
    inscr_est = fields.Char('State Inscription', size=16, copy=False, help='Em pessoas jurídicas sem o I.E. utilise a palavra "ISENTO"')
    rg_fisica = fields.Char('RG', size=16, copy=False)
    inscr_mun = fields.Char('Municipal Inscription', size=18)
    suframa = fields.Char('Suframa', size=18)
    legal_name = fields.Char('Legal Name', size=60, help="Name used in fiscal documents")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=_default_country)
    ibge_code = fields.Char(related='country_id.ibge_code')
    city_id = fields.Many2one('res.state.city', 'City', domain="[('state_id','=',state_id)]")
    city_name = fields.Char(related="city_id.name")
    district = fields.Char('District', size=32)
    number = fields.Char('Number', size=10)
    type = fields.Selection(selection_add=[('branch', 'Branch')])
    carrier = fields.Boolean('Transportadora', default=False)
    rntrc = fields.Char(string='RNTRC Code', size=10, help="Registro Nacional de Transportadores Rodoviários de Carga")
    cei = fields.Char(string="CEI Code", size=12)
    union_entity_code = fields.Char(string="Union Entity code")
    pix_key_ids = fields.One2many(string="Pix Keys", comodel_name="res.partner.pix", inverse_name="partner_id", help="Keys for Brazilian instant payment (pix)")
    # state_tax_number_ids = fields.One2many(string="Others State Tax Number",  comodel_name="state.tax.numbers", inverse_name="partner_id")
    
    display_name = fields.Char(compute='_compute_nw_display_name', store=True, index=True)

    _sql_constraints = [
        ('res_partner_cnpj_cpf_uniq', 'unique (cnpj_cpf)',
         _('This CPF/CNPJ number is already being used by another partner!'))
    ]

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'branch':
            self.company_type = 'company'
            self.is_company = True
            cnpj_cpf = re.sub('[^0-9]', '', self.parent_id.cnpj_cpf or '') 
            self.cnpj_cpf = cnpj_cpf[:8]
            self.legal_name = self.parent_id.legal_name
            self.name = self.parent_id.name
        else:
            self.company_type = 'person'
            self.is_company = False
            self.cnpj_cpf = False

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name', 'legal_name')
    def _compute_nw_display_name(self):
        diff = dict(show_address=None, show_address_only=None, show_email=None)
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            partner.display_name = names.get(partner.id)

    def name_get(self):
        res = []
        for partner in self:
            name = ''
            if bool(partner.parent_id) and partner.type in ['delivery','invoice']:
                type = _(dict(partner._fields['type'].selection).get(partner.type))
                name = '%s, %s %s' % (partner.parent_id.name or partner.parent_id.legal_name or '', type or '', partner.zip)
            else:
                if partner.company_type == 'company':
                    if len(partner.parent_id) > 0:
                        if partner.type == 'branch':
                            name = '%s, Filial %s' % (partner.parent_id.name or partner.parent_id.legal_name or '', 
                                                      partner.name or partner.legal_name or '')
                        else:
                            name = '%s, %s' % (partner.parent_id.name or partner.parent_id.legal_name or '', 
                                               partner.name or partner.legal_name or '')
                    else:
                        if bool(partner.legal_name):
                            name = '[%s], %s' % (partner.name or '', partner.legal_name or '')
                        else:
                            name = partner.name or partner.legal_name or ''
                else:
                    if not partner.parent_id:
                        if partner.type in ['invoice', 'delivery', 'other']:
                            name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                        else:
                            name = partner.name or ''
                    else:
                        name = "%s, %s" % (partner.parent_id.name or partner.parent_id.legal_name, partner.name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            elif self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            elif self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))
        return res

    def _display_address(self, without_company=False):
        address = self

        if address.country_id and address.country_id.code != 'BR':
            # this ensure other localizations could do what they want
            return super(ResPartner, self)._display_address(
                without_company=False)
        else:
            address_format = (
                address.country_id and address.country_id.address_format or
                "%(street)s\n%(street2)s\n%(city)s %(state_code)s"
                "%(zip)s\n%(country_name)s")
            args = {
                'state_code': address.state_id and address.state_id.code or '',
                'state_name': address.state_id and address.state_id.name or '',
                'country_code': address.country_id and
                address.country_id.code or '',
                'country_name': address.country_id and
                address.country_id.name or '',
                'company_name': address.parent_id and
                address.parent_id.name or '',
                'city_name': address.city_id and
                address.city_id.name or '',
            }
            address_field = ['title', 'street', 'street2', 'zip', 'city',
                             'number', 'district']
            for field in address_field:
                args[field] = getattr(address, field) or ''
            if without_company:
                args['company_name'] = ''
            elif address.parent_id:
                address_format = '%(company_name)s\n' + address_format
            return address_format % args

    @api.constrains('cnpj_cpf', 'country_id', 'is_company')
    def _check_cnpj_cpf(self):
        for partner in self:
            country_code = partner.country_id.code or ''
            if partner.type == 'contact' and partner.cnpj_cpf and (country_code.upper() == 'BR' or len(country_code) == 0):
                if partner.is_company:
                    if re.sub('[^0-9]', '', partner.cnpj_cpf) != "00000000000000" and not fiscal.validate_cnpj(partner.cnpj_cpf):
                        raise ValidationError(_('Invalid CNPJ Number!'))
                elif re.sub('[^0-9]', '', partner.cnpj_cpf) != "00000000000" and not fiscal.validate_cpf(partner.cnpj_cpf):
                    raise ValidationError(_('Invalid CPF Number!'))
        return True

    def _is_cnpj_or_cpf(self):
        self.ensure_one()
        res = False
        if fiscal.validate_cnpj(self.cnpj_cpf):
            res = 'CNPJ'
        elif fiscal.validate_cpf(self.cnpj_cpf):
            res = 'CPF'
        return res

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

    @api.constrains('inscr_est', 'state_id', 'is_company')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise
        :Return: True or False."""
        for partner in self:
            if not partner.inscr_est or partner.inscr_est == 'ISENTO' \
                    or not partner.is_company:
                return True
            uf = partner.state_id and partner.state_id.code.lower() or ''
            res = partner._validate_ie_param(uf, partner.inscr_est)
            if not res:
                raise ValidationError(_('Invalid State Inscription!'))
        return True

    @api.constrains('inscr_est')
    def _check_ie_duplicated(self):
        """ Check if the field inscr_est has duplicated value
        """
        self.ensure_one()
        if not self.inscr_est or self.inscr_est == 'ISENTO':
            return True
        partner_ids = self.search(
            ['&', ('inscr_est', '=', self.inscr_est), ('id', '!=', self.id)])

        if len(partner_ids) > 0:
            raise ValidationError(
                _('This State Inscription/RG number \
                  is already being used by another partner!'))
        return True

    @api.onchange('cnpj_cpf')
    def _onchange_cnpj_cpf(self):
        country_code = self.country_id.code or ''
        if self.cnpj_cpf and (country_code.upper() == 'BR' or len(country_code) == 0):
            val = re.sub('[^0-9]', '', self.cnpj_cpf)
            if self.type == 'branch' and len(val) == 8:
                cnpj_cpf = "%s.%s.%s/" % (val[0:2], val[2:5], val[5:8])
                self.cnpj_cpf = cnpj_cpf
            elif self.type == 'contact':
                if len(val) == 14:
                    cnpj_cpf = "%s.%s.%s/%s-%s"\
                        % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                    self.cnpj_cpf = cnpj_cpf
                elif not self.is_company and len(val) == 11:
                    cnpj_cpf = "%s.%s.%s-%s"\
                        % (val[0:3], val[3:6], val[6:9], val[9:11])
                    self.cnpj_cpf = cnpj_cpf
                else:
                    raise UserError(_('Verify CNPJ/CPF number'))

    @api.onchange('city_id')
    def _onchange_city_id(self):
        """ Ao alterar o campo city_id copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        """
        if self.city_id:
            self.city = self.city_id.name

    @api.onchange('zip')
    def onchange_mask_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                zip = "%s-%s" % (val[0:5], val[5:8])
                self.zip = zip

    @api.model
    def _address_fields(self):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set.
        Extenção para os novos campos do endereço """
        address_fields = super(ResPartner, self)._address_fields()
        return list(address_fields + ['city_id', 'number', 'district'])

