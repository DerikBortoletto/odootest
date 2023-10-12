
from odoo import models, fields, api
from odoo.osv import expression

class ResBank(models.Model):
    _inherit = 'res.bank'
    _order = 'short_name'

    short_name = fields.Char(required=True)
    code_bc = fields.Char(string="Brazilian Bank Code", size=3, index=True, help="Brazilian Bank Code ex.: 001 is the code of Banco do Brasil")
    ispb_number = fields.Char(string="ISPB Number", size=8)
    compe_member = fields.Boolean(string="COMPE Member", default=False)

    number = fields.Char('Number', size=10)
    street2 = fields.Char('Complement', size=128)
    district = fields.Char('District', size=32)
    city_id = fields.Many2one(comodel_name='res.state.city', string='City', domain="[('state_id','=',state_id)]")
    country_id = fields.Many2one(comodel_name='res.country', related='country', string='Country')
    state_id = fields.Many2one(comodel_name='res.country.state', related='state', string='State')
    acc_number_format = fields.Text(help="""You can enter here the format as\
        the bank accounts are referenced in ofx files for the import of bank\
        statements.\nYou can use the python patern string with the entire bank \
        account field.\nValid Fields:\n
          %(bra_number): Bank Branch Number\n
          %(bra_number_dig): Bank Branch Number's Digit\n
          %(acc_number): Bank Account Number\n
          %(acc_number_dig): Bank Account Number's Digit\n
        For example, use '%(acc_number)s' to display the field 'Bank Account \
        Number' plus '%(acc_number_dig)s' to display the field 'Bank Account \
        Number s Digit'.""", default='%(acc_number)s')

    @api.onchange('city_id')
    def onchange_city_id(self):
        """ 
            Ao alterar o campo city_id copia o nome
            do município para o campo city que é o campo nativo do módulo base
            para manter a compatibilidade entre os demais módulos que usam o
            campo city.
        """
        if self.city_id:
            self.city = self.city_id.name

    def name_get(self):
        result = []
        for bank in self:
            name = bank.short_name + (bank.code_bc and (' - ' + bank.code_bc) or '')
            result.append((bank.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code_bc', '=ilike', name + '%'), ('short_name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

