# © 2022 Alexandre Defendi - TrackTraceErp

from odoo import fields, models, api
from odoo.osv import expression

class AccountAccountTemplate(models.Model):
    _inherit = 'account.account.template'

    account_type = fields.Selection([('tax', 'Imposto'), ('income', 'Receita'), ('expense', 'Despesa')], string="Tipo Ação")
    short_code = fields.Integer(string="Código Curto", index=True)
    group_id = fields.Many2one('account.group', string="Account Group")

class AccountAccount(models.Model):
    _inherit = 'account.account'

    account_type = fields.Selection([('tax', 'Imposto'), ('income', 'Receita'), ('expense', 'Despesa')], string="Tipo Ação")
    short_code = fields.Integer(string="Código Curto", index=True)

    @api.model
    def create(self, vals):
        if bool(vals.get('company_id')):
            company = self.env['res.company'].browse(vals['company_id'])
        else:
            company = self.env.company
        if company and company.short_code_sequence_id and (not 'short_code' in vals or not vals.get('short_code')):
            vals['short_code'] = self.env['ir.sequence'].browse(company.short_code_sequence_id.id).next_by_id()
        return super(AccountAccount, self).create(vals)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            if str(name).isdecimal():
                domain = ['|', '|', ('code', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name), ('short_code', '=', name)]
            else:
                domain = ['|', ('code', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    def name_get(self):
        result = []
        for account in self:
            name = account.code + ' ' + account.name
            if bool(account.short_code):
                name = '[%s] %s' % (str(account.short_code).zfill(3),name)
            result.append((account.id, name))
        return result

class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    short_code_sequence_id = fields.Many2one('ir.sequence', help='Sequence to use in short code',
                                             check_company=True, copy=False)

    def _get_account_vals(self, company, account_template, code_acc, tax_template_ref):
        val = super(AccountChartTemplate,self)._get_account_vals(company, account_template, code_acc, tax_template_ref)
        val.update({
                'short_code': account_template.short_code,
                'account_type': account_template.account_type,
                'group_id': account_template.group_id.id,
            })
        return val

    def _load(self, sale_tax_rate, purchase_tax_rate, company):
        if bool(company) and not bool(company.short_code_sequence_id):
            company.short_code_sequence_id = self.short_code_sequence_id            
        res = super(AccountChartTemplate,self)._load(sale_tax_rate, purchase_tax_rate, company)
        return res
    # def _create_sequence(self):
    #     for template in self:
    #         vals = {
    #             'name': _('Short Code of %s') % (template.name),
    #             'code': 'SHORTCODE%s' % (template.id),
    #             'implementation': 'no_gap',
    #             'prefix': '',
    #             'suffix': '',
    #             'padding': 0}
    #         seq = self.env['ir.sequence'].create(vals)
    #         template.short_code_sequence_id = seq.id
    #
    # @api.model
    # def create(self, vals):
    #     # OVERRIDE
    #     template = super(AccountChartTemplate, self).create(vals)
    #     template._create_sequence()
    #     return template

