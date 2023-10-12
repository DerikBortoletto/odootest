# -*- coding: utf-8 -*-

import logging
import pprint
import time

import werkzeug

from odoo import http
from odoo.http import request
import urllib.parse
import urllib.request
import random


_logger = logging.getLogger(__name__)


class ZiftController(http.Controller):
    _return_url = '/payment/zift/return'
    _cancel_url = '/payment/zift/cancel'
    _exception_url = '/payment/zift/error'
    _reject_url = '/payment/zift/reject'

    @http.route([
        '/payment/zift/return',
        '/payment/zift/cancel',
        '/payment/zift/error',
        '/payment/zift/reject',
    ], type='http', auth='public', csrf=False)
    def zift_return(self, **post):
        """ Zift."""
        _logger.info('Zift: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'zift')
        post = {key.upper(): value for key, value in post.items()}
        return_url = post.get('ADD_RETURNDATA') or '/'
        return werkzeug.utils.redirect('/payment/process')

class ServiceRequest(http.Controller):

    @http.route(['/request'], type='http', auth="public", website=True, csrf=False,  methods=['POST'])
    def service_request(self, **kw):
        info_zift = request.env['payment.acquirer'].sudo().search([('provider', '=', 'zift')])
        conta_01_02 = info_zift.write_uid.last_website_so_id
        conta = info_zift.write_uid.sale_order_count
        conta_pesquisa = info_zift.write_uid.sale_order_ids.search([('id', '=', conta)])
        acesso_senha = info_zift.brq_secretkey
        acesso_login = info_zift.brq_websitekey
        sales = request.env['sale.order'].sudo().search([])

        if kw.get("valid_date") and kw.get("cvv"):
            pedido_compra = request.env['payment.acquirer'].sudo().search([('provider', '=', 'zift')])
            valor_total = str(int(float(pedido_compra.amount) * 100))
            customerAccountCode = str(random.randint(100000, 1000000))
            transactionCode = str(random.randint(1000000000, 9999999999))
            nome = kw['name']
            nome = nome.replace(" ","+")
            valid_date = kw['valid_date']
            valid_date = valid_date.replace("/","")
            cvv = kw['cvv']
            cardnumber = kw['cardnumber']
            cardnumber = cardnumber.replace(" ","")
            zipCode = kw['zipCode']
            zipCode = zipCode.replace(" ","")
            zipCode = zipCode.replace("-", "")
            state = kw['state']
            city = kw['city']
            street = kw['street']
            street = street.replace(" ","+")
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
                'accountId': accountId,
                'amount': valor_total,
                'accountType': 'R',
                'transactionIndustryType': 'RE',
                'holderType': 'P',
                'holderName': nome,
                'accountNumber': cardnumber,
                'accountAccessory': valid_date,
                'street': street,
                'csc': cvv,
                'city': city,
                'state': state,
                'zipCode': zipCode,
                'customerAccountCode': customerAccountCode,
                'transactionCode': transactionCode

            }

            data = urllib.parse.urlencode(values)
            data = data.encode('utf-8')  # data should be bytes
            req = urllib.request.Request(url, data)
            with urllib.request.urlopen(req) as response:
                the_page = response.read()
                the_page = str(the_page)
                indice = the_page.find("responseCode=")
                indice_count = int(indice) + 13
                the_page_1 = the_page[indice_count:indice_count+3]
                indice_01 = the_page.find("responseMessage=")
                indice_02 = the_page.find("&transactionId=")
                the_page_2 = the_page[int(indice_01) + 16: int(indice_02)]
                if the_page_1 == 'A01' and the_page_2 == 'Approved':
                    if len(conta_01_02) > 0:
                        conta_01_02.write({
                            'state': 'done',
                        })
                    else:
                        conta_pesquisa.write({
                            'state': 'done',
                        })
                    return werkzeug.utils.redirect('/success')
                else:
                    return werkzeug.utils.redirect('/denied')

        return request.render('payment_zift_01.request_form')


class error_page(http.Controller):
    @http.route('/denied', type='http', auth='user', website=True)
    def show_custom_webpage(self, **kw):
        return http.request.render('payment_zift_01.error_page', {})


class success_page(http.Controller):
    @http.route('/success', type='http', auth='user', website=True)
    def show_custom_webpage(self, **kw):
        return http.request.render('payment_zift_01.success_page', {})
