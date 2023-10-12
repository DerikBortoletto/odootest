
from odoo import models, fields, api, exceptions

class PasswordManager(models.Model):
    _name = 'meu_modulo_senha.password'
    _description = 'Gerenciador de Senhas'


    name = fields.Char(string='Nome', required=True)
    senha = fields.Char(string='Senha', required=True)
    senha_confirma = fields.Char(string='Senha Confirma', required=True)
    @api.constrains('senha')
    def _check_senha(self):
        for registro in self:
            if len(registro.senha) < 6:
                raise exceptions.ValidationError('A senha deve ter pelo menos 6 caracteres.')



    @api.constrains('senha_confirma')
    def _check_senha(self):
        for registro in self:
            if registro.senha_confirma != registro.senha:
                raise exceptions.ValidationError('A senha deve ser igual a outra')

    @api.constrains('senha')
    def _check_senha_2(self):
        senhas = self.env['meu_modulo_senha.password'].sudo().search([])
        lista_senhas = []
        for i in senhas:
            if i.id != self.id:
                lista_senhas.append(i.senha)
        for registro in self:
            if registro.senha in lista_senhas:
                raise exceptions.ValidationError('Gere uma senha diferente')