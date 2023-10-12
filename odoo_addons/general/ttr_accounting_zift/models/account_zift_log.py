import logging

from odoo import api, fields, models,  exceptions
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tests import Form
from odoo.tools.translate import _
from datetime import datetime, date, timedelta
import urllib.parse
import urllib.request
import numpy as np
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)
import random


class ZiftLog(models.Model):
    _name = "zift.log"
    _description = "Logs do Zifts"

    logs_id = fields.Many2one('account.move', string='Logs id')

    valid_date_1 = fields.Date(string='Date',)
    link_gerado = fields.Char()
    log_de_pagamento_automatico = fields.Char()
    status_de_pagamento = fields.Char()

    email_envia = fields.Char()
    data_email_valid = fields.Date(string='Your string')

class ZiftEmail(models.Model):
    _name = "zift.email"
    _description = "Email do Zifts"
    _rec_name = 'email_envia'


    email_envia = fields.Char(string='Email')



class ContractContractLine(models.Model):
    _inherit = "contract.line"

    numero_parcelas = fields.Integer(default=1)
    valor_total_dividido = fields.Float(compute='_compute_valor_total_dividido')

    def _compute_valor_total_dividido(self):
        for i in self:
            if i.numero_parcelas != 0:
                i.valor_total_dividido = i.price_subtotal / float(i.numero_parcelas)
            else:
                i.valor_total_dividido = i.price_subtotal / 1


class ContractContractContract(models.Model):
    _inherit = "contract.contract"

    observation = fields.Text(string='Obs:')
    credito = fields.Float(string="Credit", default=0.00)
    credito_auxiliar = fields.Float(string="Credit", default=0.00)
    rename = fields.Float(compute='_rename')
    logs = fields.Many2many('zift.email',string="Email")

    valid_date_start = fields.Date(string='Date', )
    senha = fields.Char(string='Password')
    name_senha = fields.Char(string='Nome')
    payment_link_contract = fields.Boolean(help='Pay Per Link')
    email_to = fields.Char()
    email_from = fields.Char()
    subject = fields.Char()
    nome_cartao = fields.Char()
    nome_cartao_back = fields.Char()
    numero_cartao_back = fields.Char()
    numero_cartao = fields.Char(string='Card Number', help='Only Numbers')
    street_1 = fields.Char()
    state_1 = fields.Char()
    city_1 = fields.Char()
    zip_1 = fields.Integer(string='Zip Code', help='Only Numbers')
    code_cvv = fields.Integer(string='Start from', help='Only Numbers')
    valid_date_1 = fields.Date(string='Your string', default=datetime.today())
    valid_date_y = fields.Selection(
        [("2023", "2023"), ("2024", "2024"), ("2025", "2025"), ("2026", "2026"), ("2027", "2028"), ("2029", "2029"),
         ("2030", "2030"), ("2031", "2031"), ("2032", "2032"), ("2033", "2033"), ("2034", "2034"), ("2035", "2035"),
         ("2036", "2036"), ("2037", "2037"), ("2038", "2038"), ("2039", "2039"), ("2040", "2040")], )
    valid_date_m = fields.Selection(
        [("01", "01"), ("02", "02"), ("03", "03"), ("04", "04"), ("05", "05"), ("06", "06"), ("07", "07"), ("08", "08"), ("09", "09"),
         ("10", "10"), ("11", "11"), ("12", "12")],
    )
    body = fields.Html('EMAIL')
    contador_data = fields.Integer(string='contador_data', default=0)
    balanco = fields.Float(compute='_balanco')
    balanco_apar = fields.Char(compute='_balanco_apar')
    balanco_conta = fields.Char(compute='_balanco_conta')
    boolean_balanco = fields.Boolean(compute='_boolean_bala')
    recurring_payment = fields.Boolean(help='Recurring Payment')


    def teste(self):
        contratos = self.env['contract.contract'].sudo().search([])
        teste = len(contratos)
        for y in contratos:
            invoices = self.env['account.move'].sudo().search([('id_contract_contract', '=', y.id)])
            data_contratos = []
            for v in invoices:
                data_contratos.append(v.date_field_pagamento)
            data_contratos = sorted(data_contratos, reverse=True)
            if len(data_contratos)> 0:
                difereeenca_dias = data_contratos[0] - date.today()
                difereeenca_dias = data_contratos[0] - date.today()

                if difereeenca_dias.days < 90 and y.recurring_payment == True:
                    invoices_values = y._prepare_recurring_invoices_values(date_ref=False)
                    value_invoice = invoices_values[0]['invoice_line_ids']
                    lista_invoices_values = []
                    lista_produtos = []
                    lista_total_dividido = []
                    lista_numero_parcelas = []
                    nome_fic = 0
                    for produtos in y.contract_line_fixed_ids:
                        lista_produtos.append(produtos.name)
                        lista_numero_parcelas.append(produtos.numero_parcelas)
                        lista_total_dividido.append(produtos.valor_total_dividido)
                        nome_fic += 1
                    for i in value_invoice:
                        lista_invoices_values.append(i)
                    for j in lista_invoices_values:
                        index_prod = lista_produtos.index(j[-1]['name'])
                        divisao = lista_total_dividido[index_prod]
                        divisao = round(divisao, 2)
                        parcelas = int(lista_numero_parcelas[index_prod])
                        count = 0
                        lista_nomes_produtos_calendar = []
                        lista_nomes_produtos_calendar.append(lista_produtos[0])
                        name_senha = y.name_senha
                        del lista_produtos[0]
                        del lista_total_dividido[0]
                        del lista_numero_parcelas[0]
                        while count < 12:
                            biblioteca = j[-1]
                            # day = j[-1]['date'].day
                            # data_mes = j[-1]['date'].month
                            # data_ano = j[-1]['date'].year

                            z = datetime.today() + timedelta(days=31)
                            day = z.day
                            data_mes = z.month
                            data_ano = z.year

                            # day = y.valid_date_start.day
                            # data_mes = y.valid_date_start.month
                            # data_ano = y.valid_date_start.year

                            if data_mes < 10:
                                data_final = str(data_ano) + '-' + '0' + str(data_mes)
                            else:
                                data_final = str(data_ano) + '-' + str(data_mes)
                            somatoria = count
                            new_date = np.datetime64(data_final) + np.timedelta64(somatoria, 'M')
                            indice = str(new_date).find("-")
                            mes = str(new_date)[indice + 1:]
                            ano = str(new_date)[:indice]
                            biblioteca.update({
                                'price_unit': divisao,
                            })
                            new_j = (0, 0, biblioteca)
                            invoices_values[0]['invoice_line_ids'] = new_j
                            moves = y.env["account.move"].create(invoices_values)
                            if day < 29:
                                prod_calendar = lista_nomes_produtos_calendar[0]
                                if mes[0] == '0':
                                    moves.update({
                                        'date_field_pagamento': date(year=int(ano), month=int(mes[1]), day=day),
                                        'payment_link': y.payment_link_contract,
                                        'nome_cartao': y.nome_cartao,
                                        'nome_cartao_back': y.nome_cartao_back,
                                        'numero_cartao_back': y.numero_cartao_back,
                                        'numero_cartao': y.numero_cartao,
                                        'street_1': y.street_1,
                                        'state_1': y.state_1,
                                        'city_1': y.city_1,
                                        'zip_1': y.zip_1,
                                        'code_cvv': y.code_cvv,
                                        'valid_date_1': y.valid_date_1,
                                        'valid_date_y': y.valid_date_y,
                                        'valid_date_m': y.valid_date_m,
                                        'body': y.body,
                                        'email_to': y.email_to,
                                        'email_from': y.email_from,
                                        'subject': y.subject,
                                        'id_contract_contract': y.id,
                                        'contract_name': y.name,
                                        'numero_da_parcela': count + 1,
                                        'numero_parcelas': parcelas,

                                    })
                                    data = date(year=int(ano), month=int(mes[1]), day=day)
                                    contador = 'Nº' + str(count + 1)

                                    y.calendar_invoice(data, prod_calendar, contador, divisao, name_senha)
                                else:
                                    moves.update({
                                        'date_field_pagamento': date(year=int(ano), month=int(mes), day=day),
                                        'payment_link': y.payment_link_contract,
                                        'nome_cartao': y.nome_cartao,
                                        'nome_cartao_back': y.nome_cartao_back,
                                        'numero_cartao_back': y.numero_cartao_back,
                                        'numero_cartao': y.numero_cartao,
                                        'street_1': y.street_1,
                                        'state_1': y.state_1,
                                        'city_1': y.city_1,
                                        'zip_1': y.zip_1,
                                        'code_cvv': y.code_cvv,
                                        'valid_date_1': y.valid_date_1,
                                        'valid_date_y': y.valid_date_y,
                                        'valid_date_m': y.valid_date_m,
                                        'body': y.body,
                                        'email_to': y.email_to,
                                        'email_from': y.email_from,
                                        'subject': y.subject,
                                        'id_contract_contract': y.id,
                                        'contract_name': y.name,
                                        'numero_da_parcela': count + 1,
                                        'numero_parcelas': parcelas,

                                    })
                                    data = date(year=int(ano), month=int(mes), day=day)
                                    contador = 'Nº' + str(count + 1)
                                    y.calendar_invoice(data, prod_calendar, contador, divisao, name_senha)

                            else:
                                prod_calendar = lista_nomes_produtos_calendar[0]
                                if mes[0] == '0':
                                    moves.update({
                                        'date_field_pagamento': date(year=int(ano), month=int(mes[1]), day=28),
                                        'payment_link': y.payment_link_contract,
                                        'nome_cartao': y.nome_cartao,
                                        'nome_cartao_back': y.nome_cartao_back,
                                        'numero_cartao_back': y.numero_cartao_back,
                                        'numero_cartao': y.numero_cartao,
                                        'street_1': y.street_1,
                                        'state_1': y.state_1,
                                        'city_1': y.city_1,
                                        'zip_1': y.zip_1,
                                        'code_cvv': y.code_cvv,
                                        'valid_date_1': y.valid_date_1,
                                        'valid_date_y': y.valid_date_y,
                                        'valid_date_m': y.valid_date_m,
                                        'body': y.body,
                                        'email_to': y.email_to,
                                        'email_from': y.email_from,
                                        'subject': y.subject,
                                        'id_contract_contract': y.id,
                                        'contract_name': y.name,
                                        'numero_da_parcela': count + 1,
                                        'numero_parcelas': parcelas,

                                    })
                                    data = date(year=int(ano), month=int(mes[1]), day=28)
                                    contador = 'Nº' + str(count + 1)
                                    y.calendar_invoice(data, prod_calendar, contador, divisao, name_senha)
                                else:
                                    moves.update({
                                        'date_field_pagamento': date(year=int(ano), month=int(mes), day=28),
                                        'payment_link': y.payment_link_contract,
                                        'nome_cartao': y.nome_cartao,
                                        'nome_cartao_back': y.nome_cartao_back,
                                        'numero_cartao_back': y.numero_cartao_back,
                                        'numero_cartao': y.numero_cartao,
                                        'street_1': y.street_1,
                                        'state_1': y.state_1,
                                        'city_1': y.city_1,
                                        'zip_1': y.zip_1,
                                        'code_cvv': y.code_cvv,
                                        'valid_date_1': y.valid_date_1,
                                        'valid_date_y': y.valid_date_y,
                                        'valid_date_m': y.valid_date_m,
                                        'body': y.body,
                                        'email_to': y.email_to,
                                        'email_from': y.email_from,
                                        'subject': y.subject,
                                        'id_contract_contract': y.id,
                                        'contract_name': y.name,
                                        'numero_da_parcela': count + 1,
                                        'numero_parcelas': parcelas,

                                    })
                                    data = date(year=int(ano), month=int(mes), day=28)
                                    contador = 'Nº' + str(count + 1)
                                    y.calendar_invoice(data, prod_calendar, contador, divisao, name_senha)

                            y._invoice_followers(moves)
                            y._compute_recurring_next_date()
                            count += 1

        # return moves


    def _balanco_apar(self):
        view = self.env['account.move'].sudo().search([('id_contract_contract', '=', self.id)])
        self.teste()
        total = 0
        total_cancel = 0
        for t in view:
            texto = "$" + " " + str(t.credito_view)
            t.write({
                'credito_view_str': texto
            })
        for i in view:
            if i.credito_view < 0:
                total += (i.credito_view)*-1
            else:
                total += (i.credito_view)
            if i.state == 'cancel':
                total -= i.amount_total_signed


        texto = "$"+" "+str(total)
        self.balanco_apar = texto

    def _balanco_conta(self):
        view = self.env['account.move'].sudo().search([('id_contract_contract', '=', self.id)])
        total = 0
        total_amount = 0
        for i in view:
            if i.state == 'posted':
                total_amount += i.amount_total_signed
            if i.credito_view < 0:
                total += (i.credito_view)*-1
            if i.credito_view > 0:
                total += (i.credito_view)
        total_final = total_amount - total
        texto = "$"+" "+str(total_final)
        self.balanco_conta = texto


    def _boolean_bala(self):
        x = self.env['account.move'].sudo().search([('id_contract_contract', '=', self.id)])
        conta = self.balanco_apar.replace("$", "")
        conta = conta.replace(" ", "")
        conta = float(conta)
        if conta >= 0:
            self.boolean_balanco = True
        else:
            self.boolean_balanco = False

    def _balanco(self):
        invoices = self.env['account.move'].sudo().search([('id_contract_contract', '=', self.id)])
        lista = []
        lista_credito = []
        invoices_cancel = invoices.search([('state', '=', "cancel")])
        invoices_2 = self.env['account.move'].sudo().search([('id_contract_contract', '=', self.id)])
        for inv in invoices_2:
            for line in inv.invoice_line_ids:
                if line.name == "Credit":
                    lista_credito.append(line.price_subtotal)
            if inv.state == "cancel":
                for line in inv.invoice_line_ids:
                    if line.name != "Credit":
                        lista.append(line.price_subtotal)
        if len(invoices_cancel) > 0:
            # for i in invoices_cancel:
            #     lista.append(i.amount_total_signed)
            if len(lista_credito)>0:
                total = (sum(lista)*-1) + (sum(lista_credito)*-1)
                self.balanco = float(total)
            else:
                self.balanco = float(sum(lista))*-1

        else:
            if len(lista_credito) > 0:
                total = (sum(lista_credito) * -1)
                self.balanco = float(total)
            else:
                self.balanco = 0.0




    @api.model
    def create(self, values):
        if values.get("numero_cartao"):
            # self.seu_nome_2 = self.partner_id.name + '-' +self.write_uid.display_name
            if values['numero_cartao'] != '****************':
                numero_cartao = values['numero_cartao']
                numero_cartao = numero_cartao.replace(".", "")
                numero_cartao = numero_cartao.replace("-", "")
                numero_cartao = numero_cartao.replace(",", "")
                numero_cartao = numero_cartao.replace(" ", "")
                numero_cartao = numero_cartao.replace("/", "")
                numero_cartao = numero_cartao.replace("_", "")
                values['numero_cartao_back'] = numero_cartao
                self.numero_cartao_back = numero_cartao
                values['numero_cartao_back'] = numero_cartao
                string_embaralhada = '****************'
                values['numero_cartao'] = string_embaralhada
        if values.get("nome_cartao"):
            if values['nome_cartao'] != '****************':
                nome_cartao = values['nome_cartao']
                nome_cartao = nome_cartao.replace(" ", "+")
                self.nome_cartao_back = nome_cartao.replace(".", "")
                nome_cartao = nome_cartao.replace("+", "")
                string_embaralhada = '****************'
                values['nome_cartao'] = string_embaralhada
        return super(ContractContractContract, self).create(values)


    def write(self, values):
        if len(self.env['account.move'].sudo().search([('id_contract_contract', '=', self.id)])) > 0:
            if values.get("credito"):
                if not values.get("observation"):
                    raise exceptions.ValidationError('Fill in the comment field')
                if values.get("observation"):
                    descri = values["observation"]
                    space = descri.replace(" ", "")
                    if len(space) == 0:
                        raise exceptions.ValidationError('Fill in the comment field')
                    else:
                        self.message_post(
                            body=_(
                                " -Credit Created: \n %s \n"
                                " - Credit: %s \n"
                            )
                                 % (str(values["observation"]), str(values["credito"]))
                        )
                self.credito_auxiliar = values['credito']
                lista_acount = []
                for lista in self.env['account.move'].sudo().search([('id_contract_contract', '=', self.id)]):
                    lista_acount.append(int(lista.id))
                lista_acount = sorted(lista_acount)
                lista_obeject = []
                for lo in lista_acount:
                    lista_obeject.append(self.env['account.move'].sudo().search([('id', '=', lo)]))
                for i in lista_obeject:
                    dias = i.date_field_pagamento - date.today()
                    if dias.days >= 0:
                        if i.payment_state == 'not_paid' and i.state == 'draft':
                            for t in i.invoice_line_ids:
                                lista_product = []
                                for s in i.invoice_line_ids:
                                    if s.product_id != False:
                                        lista_product.append(s.product_id)
                                for f in lista_product:
                                    if f.id == False:
                                        lista_product.remove(f)
                                if self.credito_auxiliar > 0:
                                    subtracao = float(self.credito_auxiliar) - float(t.price_unit)
                                    if subtracao > 0 and subtracao != self.credito_auxiliar:
                                        i.write({
                                            'invoice_line_ids': [(0, 0, {
                                                'product_id': lista_product[0],
                                                'name': 'Credit',
                                                'account_id': t.account_id,
                                                 'price_unit': (t.price_unit)*(-1),
                                            })],
                                        })
                                        i.write({
                                            'credito_view': (t.price_unit)*(-1),
                                            'observation_credi': self.observation,
                                            'date_field_credit': date.today(),
                                        })
                                        self.credito_auxiliar = subtracao
                                    if subtracao < 0:
                                        i.write({
                                            'invoice_line_ids': [(0, 0, {
                                                'product_id': lista_product[0],
                                                'name': 'Credit',
                                                'account_id': t.account_id,
                                                'price_unit': (self.credito_auxiliar)*(-1)
                                            })],
                                        })
                                        i.write({
                                            'credito_view': (self.credito_auxiliar)*(-1),
                                            'observation_credi': self.observation,
                                            'date_field_credit': date.today(),
                                        })
                                        self.credito_auxiliar = 0
                                    if subtracao == 0:
                                        i.write({
                                            'invoice_line_ids': [(0, 0, {
                                                'product_id': lista_product[0],
                                                'name': 'Credit',
                                                'account_id': t.account_id,
                                                 'price_unit': (t.price_unit)*(-1),
                                            })],
                                        })
                                        i.write({
                                            'credito_view': (t.price_unit)*(-1),
                                            'observation_credi': self.observation,
                                            'date_field_credit':date.today(),
                                        })
                                        self.credito_auxiliar = 0

        if len(self.env['account.move'].sudo().search([('id_contract_contract', '=', self.id)])) == 0:
            if values.get("credito"):
                self.credito_auxiliar = 0
                values['credito'] = 0
        if values.get("numero_cartao"):
            # self.seu_nome_2 = self.partner_id.name + '-' +self.write_uid.display_name
            if values['numero_cartao'] != '****************':
                numero_cartao = values['numero_cartao']
                numero_cartao = numero_cartao.replace(".", "")
                numero_cartao = numero_cartao.replace("-", "")
                numero_cartao = numero_cartao.replace(",", "")
                numero_cartao = numero_cartao.replace(" ", "")
                numero_cartao = numero_cartao.replace("/", "")
                numero_cartao = numero_cartao.replace("_", "")
                self.numero_cartao_back = numero_cartao
                string_embaralhada = '****************'
                values['numero_cartao'] = string_embaralhada
        if values.get("nome_cartao"):
            if values['nome_cartao'] != '****************':
                nome_cartao = values['nome_cartao']
                nome_cartao = nome_cartao.replace(" ", "+")
                self.nome_cartao_back = nome_cartao.replace(".", "")
                nome_cartao = nome_cartao.replace("+", "")
                string_embaralhada = '****************'
                values['nome_cartao'] = string_embaralhada

        return super(ContractContractContract, self).write(values)

    @api.constrains('senha')
    def _check_senha_2(self):
        senhas = self.env['meu_modulo_senha.password'].sudo().search([])
        lista_senhas = ["xaxaxaxaxaxaxaxaxaxaxax"]
        for i in senhas:
                lista_senhas.append(i.senha)
        for registro in self:
            if registro.senha not in lista_senhas:
                # raise exceptions.ValidationError('Senha Errada')
                pass
            else:
                pass
                # if registro.senha != "xaxaxaxaxaxaxaxaxaxaxax":
                #     nome = self.env['meu_modulo_senha.password'].sudo().search([('senha', '=', registro.senha)])
                #     self.name_senha = nome.name


    def email_valid(self):
        for i in self.env['calendar.event'].search([('start_date', '=', date.today())]):
            if "Days to end of contract:" in i.name:
                    for j in self.env['zift.email'].search([]):
                        email = j.email_envia.replace(" ", "")
                        template = self.env.ref('ttr_accounting_zift.send_mail_zift')
                        body_html = i.description
                        email_values = {
                            "subject": i.name,
                            "email_from": email,
                            "email_to": email,
                            "body_html": body_html,
                        }
                        template.send_mail(self.id, force_send=True, email_values=email_values)

    def pass_reset(self):
        senhas = self.env['contract.contract'].sudo().search([])
        for i in senhas:
            i.write({'senha': "xaxaxaxaxaxaxaxaxaxaxax"})






    def recurring_create_invoice(self):
        """
        This method triggers the creation of the next invoices of the contracts
        even if their next invoicing date is in the future.
        """
        invoice = self._recurring_create_invoice()
        if invoice:
            self.message_post(
                body=_(
                    "Contract manually invoiced: "
                    '<a href="#" data-oe-model="%s" data-oe-id="%s">Invoice'
                    "</a>"
                )
                % (invoice._name, invoice.id)
            )
        return invoice

    def _rename(self):
        lista_acount = []
        for lista in self.env['account.move'].sudo().search([('id_contract_contract', '=', self.id)]):
            lista_acount.append(int(lista.id))
        lista_acount = sorted(lista_acount)
        lista_obeject = []
        for lo in lista_acount:
            lista_obeject.append(self.env['account.move'].sudo().search([('id', '=', lo)]))
        if len(lista_obeject) > 0:
            if self.contador_data == 0:
                self.write({
                    'contador_data': 1,
                })
                if len(lista_obeject) > 1:
                    data_ultimo = lista_obeject[-1].date_field_pagamento
                    data_penultimo = lista_obeject[-2].date_field_pagamento
                    diferenca_data = data_ultimo - data_penultimo
                    if diferenca_data.days >= 0:
                        trinta = data_ultimo - timedelta(30)
                        sixty = data_ultimo - timedelta(60)
                        noventa = data_ultimo - timedelta(90)
                        self.calendar_invoice_contracts(trinta, 30)
                        self.calendar_invoice_contracts(sixty, 60)
                        self.calendar_invoice_contracts(noventa, 90)
                    if diferenca_data.days < 0:
                        trinta = data_penultimo - timedelta(30)
                        sixty = data_penultimo - timedelta(60)
                        noventa = data_penultimo - timedelta(90)
                        self.calendar_invoice_contracts(trinta, 30)
                        self.calendar_invoice_contracts(sixty, 60)
                        self.calendar_invoice_contracts(noventa, 90)
                else:
                    data_ultimo = lista_obeject[0].date_field_pagamento
                    trinta = data_ultimo - timedelta(30)
                    sixty = data_ultimo - timedelta(60)
                    noventa = data_ultimo - timedelta(90)
                    self.calendar_invoice_contracts(trinta, 30)
                    self.calendar_invoice_contracts(sixty, 60)
                    self.calendar_invoice_contracts(noventa, 90)

        self.rename = 0.0

    def calendar_invoice_contracts(self, date, number):
        participants = [self.write_uid.partner_id.id]
        nome_completo = self.name + " " + "|" + " " + "Days to end of contract:" + " " + str(number)
        descricao = 'Information:\n' + 'Customer Contracts:' + " " + self.name + '\n' + "Days to end of contract:" + " " + str(date)
        event = {
            'name': 'Payment Alarm %s' % nome_completo,
            'alarm_type': 'notification',
            'duration': 60,
        }
        data = {
            'name': 'Contract: %s' % nome_completo,
            'start_date': date,
            'stop_date': date,
            'allday': True,
            'location': ' Customer Contracts ID #%s' % self.id,
            'description': descricao,
            'user_id': self.write_uid.partner_id.id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)], limit=1).id,
            'partner_ids': [(6, False, participants)],
            'alarm_ids': [(0,0,event)],
        }
        # self.env['calendar.event'].create(data)




    def calendar_invoice(self, date, prod_calendar, contador, divisao, name_senha=None):
        participants = [self.write_uid.partner_id.id]
        nome_completo = self.name + " " + prod_calendar + " " + contador
        descricao = 'Information:\n' + 'Customer Contracts:' + " " + self.name + '\n' + 'Pay Day:' + " " + str(date) +  '\n' + 'Product:' + " " +  prod_calendar + '\n' + 'Invoice:' + " " + contador + '\n' + 'Price:' + " " + str(divisao) + '\n'
        event = {
            'name': 'Payment Alarm %s' % nome_completo,
            'alarm_type': 'notification',
            'duration': 60,
        }
        data = {
            'name': 'Invoice: %s' % nome_completo,
            'start_date': date,
            'stop_date': date,
            'allday': True,
            'location': ' Customer Contracts ID #%s' % self.id,
            'description': descricao,
            'user_id': self.write_uid.partner_id.id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)], limit=1).id,
            'partner_ids': [(6, False, participants)],
            'alarm_ids': [(0,0,event)],
        }
        # self.env['calendar.event'].create(data)


    def _recurring_create_invoice(self, date_ref=False):
        # if self.senha == "xaxaxaxaxaxaxaxaxaxaxax":
        #     raise exceptions.ValidationError('Rescreva sua senha')
        invoices_values = self._prepare_recurring_invoices_values(date_ref)
        value_invoice = invoices_values[0]['invoice_line_ids']
        lista_invoices_values = []
        lista_produtos = []
        lista_total_dividido = []
        lista_numero_parcelas = []
        nome_fic = 0
        for produtos in self.contract_line_fixed_ids:
            lista_produtos.append(produtos.name)
            lista_numero_parcelas.append(produtos.numero_parcelas)
            lista_total_dividido.append(produtos.valor_total_dividido)
            nome_fic +=1
        for i in value_invoice:
            lista_invoices_values.append(i)
        for j in lista_invoices_values:
            index_prod = lista_produtos.index(j[-1]['name'])
            divisao = lista_total_dividido[index_prod]
            divisao = round(divisao, 2)
            parcelas = int(lista_numero_parcelas[index_prod])
            count = 0
            lista_nomes_produtos_calendar = []
            lista_nomes_produtos_calendar.append(lista_produtos[0])
            name_senha = self.name_senha
            del lista_produtos[0]
            del lista_total_dividido[0]
            del lista_numero_parcelas[0]
            while count < parcelas:
                biblioteca = j[-1]
                # day = j[-1]['date'].day
                # data_mes = j[-1]['date'].month
                # data_ano = j[-1]['date'].year
                day = self.valid_date_start.day
                data_mes = self.valid_date_start.month
                data_ano = self.valid_date_start.year
                if data_mes < 10:
                    data_final = str(data_ano) + '-' + '0' + str(data_mes)
                else:
                    data_final = str(data_ano) + '-' + str(data_mes)
                somatoria = count
                new_date = np.datetime64(data_final) + np.timedelta64(somatoria, 'M')
                indice = str(new_date).find("-")
                mes = str(new_date)[indice+1:]
                ano = str(new_date)[:indice]
                biblioteca.update({
                    'price_unit': divisao,
                })
                new_j = (0,0,biblioteca)
                invoices_values[0]['invoice_line_ids'] = new_j
                moves = self.env["account.move"].create(invoices_values)
                if day < 29:
                    prod_calendar = lista_nomes_produtos_calendar[0]
                    if mes[0] == '0':
                        moves.update({
                            'date_field_pagamento': date(year=int(ano), month=int(mes[1]), day=day),
                            'payment_link': self.payment_link_contract,
                            'nome_cartao': self.nome_cartao,
                            'nome_cartao_back': self.nome_cartao_back,
                            'numero_cartao_back': self.numero_cartao_back,
                            'numero_cartao': self.numero_cartao,
                            'street_1':self.street_1,
                            'state_1': self.state_1,
                            'city_1': self.city_1,
                            'zip_1': self.zip_1,
                            'code_cvv': self.code_cvv,
                            'valid_date_1': self.valid_date_1,
                            'valid_date_y': self.valid_date_y,
                            'valid_date_m': self.valid_date_m,
                            'body': self.body,
                            'email_to': self.email_to,
                            'email_from': self.email_from,
                            'subject': self.subject,
                            'id_contract_contract': self.id,
                            'contract_name': self.name,
                            'numero_da_parcela': count + 1,
                            'numero_parcelas': parcelas,


                        })
                        data = date(year=int(ano), month=int(mes[1]), day=day)
                        contador = 'Nº' + str(count + 1)

                        self.calendar_invoice(data, prod_calendar, contador, divisao, name_senha)
                    else:
                        moves.update({
                            'date_field_pagamento': date(year=int(ano), month=int(mes), day=day),
                            'payment_link': self.payment_link_contract,
                            'nome_cartao': self.nome_cartao,
                            'nome_cartao_back': self.nome_cartao_back,
                            'numero_cartao_back': self.numero_cartao_back,
                            'numero_cartao': self.numero_cartao,
                            'street_1': self.street_1,
                            'state_1': self.state_1,
                            'city_1': self.city_1,
                            'zip_1': self.zip_1,
                            'code_cvv': self.code_cvv,
                            'valid_date_1': self.valid_date_1,
                            'valid_date_y': self.valid_date_y,
                            'valid_date_m': self.valid_date_m,
                            'body': self.body,
                            'email_to': self.email_to,
                            'email_from': self.email_from,
                            'subject': self.subject,
                            'id_contract_contract': self.id,
                            'contract_name': self.name,
                            'numero_da_parcela': count + 1,
                            'numero_parcelas': parcelas,


                        })
                        data = date(year=int(ano), month=int(mes), day=day)
                        contador = 'Nº' + str(count + 1)
                        self.calendar_invoice(data, prod_calendar, contador, divisao, name_senha)

                else:
                    prod_calendar = lista_nomes_produtos_calendar[0]
                    if mes[0] == '0':
                        moves.update({
                            'date_field_pagamento': date(year=int(ano), month=int(mes[1]), day=28),
                            'payment_link': self.payment_link_contract,
                            'nome_cartao': self.nome_cartao,
                            'nome_cartao_back': self.nome_cartao_back,
                            'numero_cartao_back': self.numero_cartao_back,
                            'numero_cartao': self.numero_cartao,
                            'street_1': self.street_1,
                            'state_1': self.state_1,
                            'city_1': self.city_1,
                            'zip_1': self.zip_1,
                            'code_cvv': self.code_cvv,
                            'valid_date_1': self.valid_date_1,
                            'valid_date_y': self.valid_date_y,
                            'valid_date_m': self.valid_date_m,
                            'body': self.body,
                            'email_to': self.email_to,
                            'email_from': self.email_from,
                            'subject': self.subject,
                            'id_contract_contract': self.id,
                            'contract_name': self.name,
                            'numero_da_parcela': count + 1,
                            'numero_parcelas': parcelas,

                        })
                        data = date(year=int(ano), month=int(mes[1]), day=28)
                        contador = 'Nº' + str(count + 1)
                        self.calendar_invoice(data, prod_calendar, contador, divisao, name_senha)
                    else:
                        moves.update({
                            'date_field_pagamento': date(year=int(ano), month=int(mes), day=28),
                            'payment_link': self.payment_link_contract,
                            'nome_cartao': self.nome_cartao,
                            'nome_cartao_back': self.nome_cartao_back,
                            'numero_cartao_back': self.numero_cartao_back,
                            'numero_cartao': self.numero_cartao,
                            'street_1': self.street_1,
                            'state_1': self.state_1,
                            'city_1': self.city_1,
                            'zip_1': self.zip_1,
                            'code_cvv': self.code_cvv,
                            'valid_date_1': self.valid_date_1,
                            'valid_date_y': self.valid_date_y,
                            'valid_date_m': self.valid_date_m,
                            'body': self.body,
                            'email_to': self.email_to,
                            'email_from': self.email_from,
                            'subject': self.subject,
                            'id_contract_contract': self.id,
                            'contract_name': self.name,
                            'numero_da_parcela': count + 1,
                            'numero_parcelas': parcelas,

                        })
                        data = date(year=int(ano), month=int(mes), day=28)
                        contador = 'Nº' + str(count + 1)
                        self.calendar_invoice(data, prod_calendar, contador, divisao, name_senha)

                self._invoice_followers(moves)
                self._compute_recurring_next_date()
                count += 1



        return moves




