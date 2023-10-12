import logging

from odoo import api, fields, models,  exceptions
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tests import Form
from odoo.tools.translate import _
from datetime import datetime, date, timedelta
import urllib.parse
import urllib.request
import random
from datetime import date

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = 'ir.cron'


class ContractContract(models.Model):
    _inherit = "account.move"

    logs = fields.One2many('zift.log', 'email_envia', string='Logs')

    id_contract_contract = fields.Integer()

    current_user_1 = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)
    seu_nome = fields.Char()
    seu_nome_2 = fields.Char()
    date_field_inicio = fields.Date(string='Your string', default=datetime.today())
    date_field_fim = fields.Date(string='Your string',)
    date_field_pagamento = fields.Date(string='Your string', )
    payday = fields.Integer(string='Start from', default=1)
    payment_link = fields.Boolean(help='Pay Per Link')
    payment_per_period = fields.Boolean(help='Pay Per Month')

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
    valid_date_y = fields.Selection([("2023", "2023"), ("2024", "2024"), ("2025", "2025"), ("2026", "2026"),("2027", "2028"),("2029", "2029"),("2030", "2030"),("2031", "2031"), ("2032", "2032"),("2033", "2033"), ("2034", "2034"), ("2035", "2035"), ("2036", "2036"),("2037", "2037"),("2038", "2038") ,("2039", "2039"),("2040", "2040")], )
    valid_date_m = fields.Selection(
        [("01", "01"), ("02", "02"), ("03", "03"), ("04", "04"),("05", "05"),("06", "06"),("07", "07"),("08", "08"), ("09", "09"),("10", "10"), ("11", "11"),("12", "12")],
    )

    link = fields.Char()
    body = fields.Html('EMAIL')
    email_to = fields.Char()
    subject = fields.Char()
    email_from = fields.Char()

    name_automatic = fields.Char()
    numberOfUpdates = fields.Integer('Number of updates',
                                     help='The number of times the scheduler has run and updated this field')
    lastModified = fields.Date('Last updated')

    controle = fields.Boolean(default=False)
    parcela = fields.Char()
    transactionId = fields.Char(string='TransactionId')
    observation = fields.Text(string='Obs:')
    contador = fields.Integer()

    value_ga = fields.Float(string="Value Draft", compute='value_grafic')
    value_go = fields.Float(string="Incoming Payments")
    value_feito = fields.Float(string="Payments received")

    contract_name = fields.Char()
    numero_da_parcela = fields.Integer()
    date_field_refund = fields.Date(string='Your string')
    numero_parcelas = fields.Integer(default=1)
    numero_parcelas_2 = fields.Integer(default=0)
    credito_view = fields.Float(string="credito_view")
    credito_view_str = fields.Char(string="credito_view")
    observation_credi = fields.Text(string='Obs:')
    date_field_credit = fields.Date(string='Your string', )
    booleand = fields.Boolean(default=True)
    value_refund = fields.Float(string="Payments received", default=0.0)
    tentativa = fields.Integer(string='tentativa', default=0)
    paid = fields.Char(string='Invoice status', default="Not Paid")


    @api.onchange('date_field_pagamento')
    def _tentativa(self):
        invoices = self.env['account.move'].sudo().search([('id', '=', self.ids)])
        invoices.write({
            'tentativa': 0
        })


    def value_grafic(self):
        dash = self.env['ks_dashboard_ninja.board'].search([])
        if len(self.env['ks_dashboard_ninja.board'].search([('name', '=', 'Dashboard Zift')])) == 0:
            dash.create({
                'name': 'Dashboard Zift',
                'ks_dashboard_menu_name': 'Dashboard Zift',
                'ks_dashboard_default_template': 0,
                'ks_dashboard_active': True,
                'ks_set_interval': '15000',
                'ks_date_filter_selection': 'l_none',
            })

        self.value_ga = 0







    def update_state(self):
        data = date.today().strftime('%Y-%m-%d')
        data_teste = date.today()
        dia_invoice = self.env['account.move'].search([('date_field_pagamento', '=', data_teste)])
        for i in dia_invoice:
            ver = 0
            for veri_total in i.invoice_line_ids:
                ver += veri_total.price_subtotal
            if i.state !='posted' and ver > 0:
                if i.payment_link == True:
                    total = 0.0

                    if i.controle == False and i.tentativa < 3:
                        i.write({
                            'tentativa': int(int(i.tentativa) + 1)
                        })
                        for j in i.invoice_line_ids:
                            total = total + j.price_subtotal
                        value = total
                        value = str(int(value * 100))
                        info_zift = self.env['payment.acquirer'].sudo().search([('provider', '=', 'zift')])
                        acesso_senha = info_zift.brq_secretkey
                        acesso_login = info_zift.brq_websitekey
                        accountId = info_zift.account_id
                        brq_url = info_zift.brq_url
                        url = ""
                        if brq_url:
                            url = brq_url
                        else:
                            url = 'https://sandbox-secure.zift.io/gates/xurl?'
                        values = {
                            'requestType': 'sale',
                            'userName': acesso_login,
                            'password': acesso_senha,
                            'processingMode': 'queue',
                            'transactionIndustryType': 'RE',
                            'accountType': 'R',
                            'amount': value,
                            'accountId': accountId,
                            'notifyURL': 'https://zift.io/',
                            'cancelURL': 'https://zift.io/',
                            'returnURL': 'https://zift.io/',
                            'postNotifyURL': 'https://zift.io/'

                        }

                        data = urllib.parse.urlencode(values)
                        data = data.encode('utf-8')  # data should be bytes
                        req = urllib.request.Request(url, data)
                        with urllib.request.urlopen(req) as response:
                            the_page = str(response.read())
                            indice = the_page.find("requestId=")
                            the_page = the_page[indice + 10:-1]

                        link_message = 'https://sandbox-secure.zift.io/gates/redirects/' + the_page
                        i.link = 'https://sandbox-secure.zift.io/gates/redirects/' + the_page
                        template = i.env.ref('ttr_accounting_zift.send_mail_zift')
                        body_html = i.body + "\n" + "\n" + "Payment Link: " + link_message
                        email_values = {
                            "subject": i.subject,
                            "email_from": i.email_from,
                            "email_to": i.email_to,
                            "body_html": body_html,
                        }
                        template.send_mail(i.id, force_send=True, email_values=email_values)

                        i.message_post(
                            body=_('<b>Payment Link!</b> : <a href="%s">Link Zift</a>') % (
                                     link_message)
                        )
                        i.write({'controle': True})
                else:
                    total = 0.0

                    if i.tentativa < 3:
                        if i.controle == False:
                            i.write({
                                'tentativa': int(int(i.tentativa) + 1)
                            })
                            for j in i.invoice_line_ids:
                                total = total + j.price_subtotal
                            value = total
                            value = str(int(value * 100))
                            info_zift = self.env['payment.acquirer'].sudo().search([('provider', '=', 'zift')])
                            acesso_senha = info_zift.brq_secretkey
                            acesso_login = info_zift.brq_websitekey
                            accountId = info_zift.account_id
                            customerAccountCode = str(random.randint(100000, 1000000))
                            transactionCode = str(random.randint(1000000000, 9999999999))
                            h = i
                            cardnumber = i.numero_cartao_back
                            verificacao = (type(cardnumber) is str)
                            verificacao_1 = (type(i.city_1) is str)
                            verificacao_2 = (type(i.street_1) is str)
                            if verificacao == True and verificacao_1 == True and verificacao_2 == True:
                                cardnumber = cardnumber.replace(" ", "")
                                cardnumber = cardnumber.replace(".", "")
                                cardnumber = cardnumber.replace("-", "")
                                cardnumber = cardnumber.replace("_", "")
                                cardnumber = cardnumber.replace("/", "")
                                cardnumber = cardnumber.replace(",", "")
                                cardnumber = cardnumber.replace(";", "")
                                cardnumber = cardnumber.replace(":", "")
                                nome= i.nome_cartao_back
                                city = i.city_1
                                city = city.replace(" ", "+")
                                mes = i.valid_date_m
                                ano = i.valid_date_y[2:]
                                valid_date = str(mes)+str(ano)
                                cvv = str(i.code_cvv)
                                cvv = cvv.replace(" ", "")
                                street = i.street_1
                                street = street.replace(" ", "+")
                                state = i.state_1
                                state = state.replace(" ", "+")
                                zipCode = str(i.zip_1)
                                info_zift = self.env['payment.acquirer'].sudo().search([('provider', '=', 'zift')])
                                brq_url = info_zift.brq_url
                                url = ""
                                if brq_url:
                                    url = brq_url
                                else:
                                    url = 'https://sandbox-secure.zift.io/gates/xurl?'
                                values = {
                                    'requestType': 'sale',
                                    'userName': str(acesso_login),
                                    'password': str(acesso_senha),
                                    'accountId': str(accountId),
                                    'amount': str(value),
                                    'accountType': 'R',
                                    'transactionIndustryType': 'RE',
                                    'holderType': 'P',
                                    'holderName': nome,
                                    'accountNumber': str(cardnumber),
                                    'accountAccessory': str(valid_date),
                                    'street': str(street),
                                    'csc': str(cvv),
                                    'city': str(city),
                                    'state': str(state),
                                    'zipCode': str(zipCode),
                                    'customerAccountCode': str(customerAccountCode),
                                    'transactionCode': str(transactionCode)

                                }


                                data = urllib.parse.urlencode(values)
                                data = data.encode('utf-8')  # data should be bytes
                                req = urllib.request.Request(url, data)
                                with urllib.request.urlopen(req) as response:
                                    the_page = response.read()
                                    the_page = the_page.decode("utf-8")
                                    the_page = str(the_page)
                                    indice = the_page.find("responseCode=")
                                    indice_count = int(indice) + 13
                                    the_page_1 = the_page[indice_count:indice_count + 3]
                                    indice_01 = the_page.find("&responseMessage=")
                                    indice_02 = the_page.find("&transactionId=")
                                    the_page_2 = the_page[int(indice_01) + 17: int(indice_02)]
                                    transactionId = the_page.find("&transactionId=")
                                    transactionCode = the_page.find("&transactionCode=")
                                    transactionId = the_page[int(transactionId) + 15: int(transactionCode)]
                                    providerresponsemessage = the_page.find("&providerResponseMessage=")
                                    providerresponsemessage_1 = the_page.find("&networkTransactionId=")
                                    providerresponsemessage = the_page[int(providerresponsemessage) + 25: int(providerresponsemessage_1)]
                                    originalamount = the_page.find("&originalAmount=")
                                    originalamount_1 = the_page.find("&warningCode")
                                    originalamount = the_page[int(originalamount) + 16: int(originalamount_1)]
                                    # originalamount = ((float(originalamount))/100)
                                    # originalamount = round(originalamount, 2)
                                    data_str = str(data)
                                    trans_value = data_str.find("&transactionCode")
                                    trans_value_2 = data_str[int(trans_value)+17: -1]
                                i.message_post(
                                    body=_(
                                        " - Response Message: %s \n"
                                        " - TransactionId: %s \n"
                                        " - Provider Response: Message %s \n"
                                        " - Original Amount: %s \n"
                                        " - Response Code: %s \n"
                                    )
                                         %(str(the_page_2), str(transactionId), str(providerresponsemessage), str(originalamount), str(the_page_1))
                                    )
                                i.write({'transactionId': str(transactionId)})
                                if str(the_page_1) == 'A01':
                                    i.action_post()
                                    i.write({'controle': True,
                                             'numero_parcelas_2': int(self.numero_parcelas_2 + 1),
                                             'paid': "Paid"
                                             })


        print(data)
        pass



    def write(self, values):
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

        return super(ContractContract, self).write(values)

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
        return super(ContractContract, self).create(values)

    def refund_link_zift(self):
        info_zift = self.env['payment.acquirer'].sudo().search([('provider', '=', 'zift')])
        acesso_senha = info_zift.brq_secretkey
        acesso_login = info_zift.brq_websitekey
        accountId = info_zift.account_id
        brq_url = info_zift.brq_url
        url = ""
        if brq_url:
            url = brq_url
        else:
            url = 'https://sandbox-secure.zift.io/gates/xurl?'
        values = {
            'requestType': 'refund',
            'userName': acesso_login,
            'password': acesso_senha,
            'accountId': accountId,
            'transactionId': self.transactionId

        }

        data = urllib.parse.urlencode(values)
        data = data.encode('utf-8')  # data should be bytes
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as response:
            the_page = response.read()
            the_page = str(the_page)

            if not self.observation:
                raise exceptions.ValidationError('Fill in the comment field')
            if self.observation:
                descri = self.observation
                space = descri.replace(" ", "")
                if len(space) == 0:
                    raise exceptions.ValidationError('Fill in the comment field')
                else:
                    self.message_post(
                        body=_(
                            " -Credit Created: \n %s \n"
                        )
                             % (str(self.observation))
                    )

            if the_page.find("transactionId+is+not+well-formatted") != -1:
                self.message_post(
                    body=_(
                        " *** REFUND ERROR ***"
                    )
                )
                raise exceptions.ValidationError('*** REFUND ERROR ***')


            originalTransactionCode = the_page.find("originalTransactionCode=")
            voidAmount = the_page.find("&voidAmount=")
            originalTransactionCode = the_page[int(originalTransactionCode) + 24: int(voidAmount)]

            transactionId = the_page.find("transactionId=")
            transactionCode = the_page.find("&transactionCode")
            transactionId = the_page[int(transactionId) + 14: int(transactionCode)]

            accountNumberMasked = the_page.find("&accountNumberMasked")
            voidAmount = the_page[int(voidAmount) + 12: int(accountNumberMasked)]
            voidAmount = float(voidAmount)/100

            responseCode = the_page.find("responseCode=")
            responseMessage = the_page.find("&responseMessage=")
            responseCode = the_page[int(responseCode) + 13: int(responseMessage)]

        if responseCode == 'A03':
            self.message_post(
                body=_(
                    " - Refund:"
                    " - Transaction Id: %s \n"
                    " - Original Transaction Code: %s \n"
                    " - Void Amount: %s \n"
                    " - Description: %s \n"
                )
                     % (str(transactionId), str(originalTransactionCode), str(voidAmount), str(self.observation))
            )
            self.write({
                'state': 'cancel',
                'paid': 'Canceled',
                'date_field_refund': date.today(),
                'booleand': False,
                'value_refund': self.amount_total_signed
            })
        else:
            self.message_post(
                body=_(
                    " *** REFUND ERROR ***"
                )
            )

    def button_cancel(self):
        self.write({
            'paid': 'Canceled',
        })
        return super().button_cancel()

    def button_draft(self):
        result = super().button_draft()
        self.write({
            'paid': "Not Paid",
        })

        return result



    def payment_link_zift(self):


        value = 0
        for i in self.invoice_line_ids:
            value += i.price_subtotal
        value = str(int(value*100))
        info_zift = self.env['payment.acquirer'].sudo().search([('provider', '=', 'zift')])
        acesso_senha = info_zift.brq_secretkey
        acesso_login = info_zift.brq_websitekey
        accountId = info_zift.account_id
        brq_url = info_zift.brq_url
        url = ""
        if brq_url:
            url = brq_url
        else:
            url = 'https://sandbox-secure.zift.io/gates/xurl?'
        values = {
            'requestType': 'sale',
            'userName': acesso_login ,
            'password': acesso_senha,
            'processingMode': 'queue',
            'transactionIndustryType': 'RE',
            'accountType': 'R',
            'amount': value,
            'accountId': accountId,
            'notifyURL': 'https://zift.io/',
            'cancelURL': 'https://zift.io/',
            'returnURL': 'https://zift.io/',
            'postNotifyURL': 'https://zift.io/'

        }

        data = urllib.parse.urlencode(values)
        data = data.encode('utf-8')  # data should be bytes
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as response:
            the_page = str(response.read())
            indice = the_page.find("requestId=")
            the_page = the_page[indice + 10:-1]

        self.link = 'https://sandbox-secure.zift.io/gates/redirects/' + the_page

        link_message = 'https://sandbox-secure.zift.io/gates/redirects/' + the_page
        template = self.env.ref('ttr_accounting_zift.send_mail_zift')
        body_html = self.body + "\n" + "\n" + "Payment Link: " + link_message
        email_values = {
            "subject": self.subject,
            "email_from": self.email_from,
            "email_to": self.email_to,
            "body_html": body_html,
        }
        template.send_mail(self.id, force_send=True, email_values=email_values)
        self.message_post(
            body=_('<b>Payment Link!</b> : <a href="%s">Link Zift</a> | Email Sent') % (
                link_message)
        )
        return


