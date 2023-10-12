from odoo import fields, models, api, _, exceptions
import re

class ResCompany(models.Model):
    _inherit = 'res.company'


    REGIMETRIBU = [
        ("1",  "1 - Simples Nacional"),
        ("2",  "2 - Simples Nacional - Excesso"),
        ("3",  "3 - Regime Normal"),
    ]
    
    cnpj = fields.Char('CNPJ')
    cpf = fields.Char('CPF')
    codigoCidade = fields.Char('Código IBGE')
    inscricaoEstadual = fields.Char('Inscrição Estadual')
    inscricaoMunicipal = fields.Char('Inscrição Municipal')
    nomeFantasia = fields.Char('Nome Fantasia')
    razaoSocial = fields.Char('Razão Social')
    regimeTributario = fields.Selection(
        REGIMETRIBU,
        string = "Regime Tributario"
    )


 
    @api.onchange('cnpj')
    def format_cnpj(self):
        cnpj = self.cnpj
        if self.cnpj:
            cnpj = ''.join(filter(str.isdigit, self.cnpj))  # Remove caracteres não numéricos
            if len(cnpj) != 14:
                raise exceptions.ValidationError(_('Invalid CNPJ Number!'))

            total = 0

            if len(set(cnpj)) == 1:
                raise exceptions.ValidationError(_('Invalid CNPJ Number!'))

            for i in range(12):
                total += int(cnpj[i]) * (5 - i % 6)
            digit1 = 11 - total % 11

            if digit1 >= 10:
                digit1 = 0

            total = 0
            for i in range(13):
                total += int(cnpj[i]) * (6 - i % 7)
            digit2 = 11 - total % 11
            if digit2 >= 10:
                digit2 = 0
            
            if not int(cnpj[12]) == digit1 and int(cnpj[13]) == digit2:
                raise exceptions.ValidationError(_('Invalid CNPJ Number!'))

            formatted_cnpj = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
            self.cnpj = formatted_cnpj

    

    @api.onchange('cpf')
    def _validate_cpf(self):

        if self.cpf:
        # Remove any non-digit characters
            cpf = re.sub(r'\D', '', self.cpf)

            if len(cpf) != 11:
                raise exceptions.ValidationError(_('Invalid CPF Number!'))

            
            if len(set(cpf)) == 1:
                raise exceptions.ValidationError(_('Invalid CPF Number!'))
            
            # Calculate verification digits
            total = 0
            for i in range(9):
                total += int(cpf[i]) * (10 - i)
            
            remainder = total % 11
            digit_1 = 0 if remainder < 2 else 11 - remainder

            if int(cpf[9]) != digit_1:
                raise exceptions.ValidationError(_('Invalid CPF Number!'))

            total = 0
            for i in range(10):
                total += int(cpf[i]) * (11 - i)
            
            remainder = total % 11
            digit_2 = 0 if remainder < 2 else 11 - remainder

            if int(cpf[10]) != digit_2:
                raise exceptions.ValidationError(_('Invalid CPF Number!'))

            self.cpf = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
      