from odoo import fields, models, api, _, exceptions
import re

class ResCompany(models.Model):
    _inherit = 'res.partner'

    TIPOLOGRA = [
        ("Alameda","Alameda "),
        ("Avenida","Avenida "),
        ("Chácara","Chácara "),
        ("Colônia","Colônia "),
        ("Condomínio","Condomínio "),
        ("Eqnp", "Eqnp "),
        ("Estância", "Estância "),
        ("Estrada","Estrada "),
        ("Fazenda","Fazenda "),
        ("Praça", "Praça "),
        ("Prolongamento","Prolongamento ")          ,
        ("Rodovia", "Rodovia "),
        ("Rua","Rua "),
        ("Sítio", "Sítio "),
        ("Travessa","Travessa "),
        ("Vicinal","Vicinal " ),
       
    ]


    part_cnpj = fields.Char('CNPJ')
    part_cpf = fields.Char('CPF')
    part_inscricaoEstadual = fields.Char('Inscrição Estadual')
    part_inscricaoMunicipal = fields.Char('Inscrição Municipal')
    part_cod_cidade = fields.Char('Codigo IBGE')
    insc_suframa = fields.Char('Inscricao Suframa')
    part_nomeFantasia = fields.Char('Nome Fantasia')
    codigoEstrangeiro = fields.Char('Identificação do Estrangeiro')
    part_razaoSocial = fields.Char('Razão Social')
    part_adress_num = fields.Char('Numero do Logradouro')
    part_tipoLogradouro = fields.Selection(
        TIPOLOGRA,
        string = "Tipo do Logradouro"
    )




    @api.onchange('part_cnpj')
    def format_cnpj(self):
        cnpj = self.part_cnpj
        if self.part_cnpj:
            cnpj = ''.join(filter(str.isdigit, self.part_cnpj))  # Remove caracteres não numéricos
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
            self.part_cnpj = formatted_cnpj

    

    @api.onchange('part_cpf')
    def _validate_cpf(self):

        if self.part_cpf:
        # Remove any non-digit characters
            cpf = re.sub(r'\D', '', self.part_cpf)

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

            self.part_cpf = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"