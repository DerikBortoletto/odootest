# coding: utf-8
from hashlib import sha1
import logging

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError


from odoo.tools.float_utils import float_compare
import urllib.parse
import urllib.request

_logger = logging.getLogger(__name__)


def normalize_keys_upper(data):
    """Set all keys of a dictionnary to uppercase

    zift parameters names are case insensitive
    convert everything to upper case to be able to easily detected the presence
    of a parameter by checking the uppercase key only
    """
    return {key.upper(): val for key, val in data.items()}


class AcquirerZift(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('zift', 'Zift')
    ], ondelete={'zift': 'set default'})
    brq_websitekey = fields.Char('UserNameApi', required_if_provider='zift', groups='base.group_user')
    brq_secretkey = fields.Char('PasswordApi', required_if_provider='zift', groups='base.group_user')
    brq_url = fields.Char('URL', required_if_provider='zift', groups='base.group_user')
    account_id = fields.Char('Account Id', required_if_provider='zift', groups='base.group_user')
    amount = fields.Char()

    def _get_zift_urls(self, environment):
        """ Monta a zift URLs com todos valores necessários
        """


        value = int(float(self.amount)*100)

        valuess = {
            'requestType': 'sale',
            'userName': str(self.brq_websitekey),
            'password': str(self.brq_secretkey),
            'processingMode': 'queue',
            'transactionIndustryType': 'RE',
            'accountType': 'R',
            'amount': str(value),
            'accountId': '6900001',
            'notifyURL': 'https://your-notify-url.com',
            'cancelURL': 'https://your-notify-url.com',
            'returnURL': 'https://your-notify-url.com',
            'postNotifyURL': 'https://your-notify-url.com',


        }
        brq_url = self.brq_url
        url = ""
        if brq_url:
            url = brq_url
        else:
            url = 'https://sandbox-secure.zift.io/gates/xurl?'
        data = urllib.parse.urlencode(valuess)
        data = data.encode('utf-8')  # data should be bytes
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as response:
            the_page = str(response.read())
            indice = the_page.find("requestId=")
            the_page = the_page[indice + 10:-1]
            URL_NOVA = 'http://sandbox-secure.zift.io/gates/redirects/' + the_page
            print(URL_NOVA)



        if environment == 'prod':
            return {
                'zift': '/request',

            }

        else:
            return {
                'zift': '/request',
            }

    def _zift_generate_digital_sign(self, inout, values):
        """ Generate the shasign for incoming or outgoing communications.

        :param browse acquirer: the payment.acquirer browse record. It should
                                have a shakey in shaky out
        :param string inout: 'in' (odoo contacting zift) or 'out' (zift
                             contacting odoo).
        :param dict values: transaction values

        :return string: shasign
        """
        assert inout in ('in', 'out')
        assert self.provider == 'zift'

        keys = "add_returndata Brq_amount Brq_culture Brq_currency Brq_invoicenumber Brq_return Brq_returncancel Brq_returnerror Brq_returnreject brq_test Brq_websitekey".split()

        def get_value(key):
            if values.get(key):
                return values[key]
            return ''

        values = dict(values or {})

        if inout == 'out':
            for key in list(values):
                # case insensitive keys
                if key.upper() == 'BRQ_SIGNATURE':
                    del values[key]
                    break

            items = sorted(values.items(), key=lambda pair: pair[0].lower())
            sign = ''.join('%s=%s' % (k, urls.url_unquote_plus(v)) for k, v in items)
        else:
            sign = ''.join('%s=%s' % (k, get_value(k)) for k in keys)
        # Add the pre-shared secret key at the end of the signature
        sign = sign + self.brq_secretkey
        shasign = sha1(sign.encode('utf-8')).hexdigest()
        return shasign


    def zift_form_generate_values(self, values):
        base_url = self.get_base_url()
        buckaroo_tx_values = dict(values)
        value = int(float(values['amount']) * 100)
        buckaroo_tx_values.update({
            'Brq_websitekey': self.brq_websitekey,
            'Brq_amount': value,
            'Brq_currency': 2,
            'reference': 'teste',
            'Brq_invoicenumber': '6900001',
            'brq_test': True if self.state == 'test' else False,
            'Brq_return':'teste',
            'Brq_returncancel': 'teste',
            'Brq_returnerror': 'teste',
            'Brq_returnreject': 'teste',
            'Brq_culture': (values.get('partner_lang') or 'en_US').replace('_', '-'),
            'add_returndata': buckaroo_tx_values.pop('return_url', '') or '',
            'requestType': 'sale',
            'userName': str(self.brq_websitekey),
            'password': str(self.brq_secretkey),
            'processingMode': 'queue',
            'transactionIndustryType': 'RE',
            'accountType': 'R',
            'amount': str(value),
            'accountId': '6900001',
            'notifyURL': 'https://your-notify-url.com',
            'cancelURL': 'https://your-notify-url.com',
            'returnURL': 'https://your-notify-url.com',
            'postNotifyURL': 'https://your-notify-url.com'
        })
        buckaroo_tx_values['Brq_signature'] = 'self._buckaroo_generate_digital_sign, buckaroo_tx_values)'
        self.amount = values['amount']

        return buckaroo_tx_values

    def zift_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_zift_urls(environment)['zift']


class Txzift(models.Model):
    _inherit = 'payment.transaction'

    # zift status
    _zift_valid_tx_status = [190]
    _zift_pending_tx_status = [790, 791, 792, 793]
    _zift_cancel_tx_status = [890, 891]
    _zift_error_tx_status = [490, 491, 492]
    _zift_reject_tx_status = [690]

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _zift_form_get_tx_from_data(self, data):
        """ Given a data dict coming from zift, verify it and find the related
        transaction record. """
        origin_data = dict(data)
        data = normalize_keys_upper(data)
        reference, pay_id, shasign = data.get('BRQ_INVOICENUMBER'), data.get('BRQ_PAYMENT'), data.get('BRQ_SIGNATURE')
        if not reference or not pay_id or not shasign:
            error_msg = _('Zift: received data with missing reference (%s) or pay_id (%s) or shasign (%s)') % (reference, pay_id, shasign)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = _('Zift: received data for reference %s') % (reference)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # verify shasign
        shasign_check = tx.acquirer_id._zift_generate_digital_sign('out', origin_data)
        if shasign_check.upper() != shasign.upper():
            error_msg = _('Zift: invalid shasign, received %s, computed %s, for data %s') % (shasign, shasign_check, data)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _zift_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        data = normalize_keys_upper(data)
        if self.acquirer_reference and data.get('BRQ_TRANSACTIONS') != self.acquirer_reference:
            invalid_parameters.append(('Transaction Id', data.get('BRQ_TRANSACTIONS'), self.acquirer_reference))
        # check what is buyed
        if float_compare(float(data.get('BRQ_AMOUNT', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('Amount', data.get('BRQ_AMOUNT'), '%.2f' % self.amount))
        if data.get('BRQ_CURRENCY') != self.currency_id.name:
            invalid_parameters.append(('Currency', data.get('BRQ_CURRENCY'), self.currency_id.name))

        return invalid_parameters

    def _zift_form_validate(self, data):
        data = normalize_keys_upper(data)
        status_code = int(data.get('BRQ_STATUSCODE', '0'))
        if status_code in self._zift_valid_tx_status:
            self.write({'acquirer_reference': data.get('BRQ_TRANSACTIONS')})
            self._set_transaction_done()
            return True
        elif status_code in self._zift_pending_tx_status:
            self.write({'acquirer_reference': data.get('BRQ_TRANSACTIONS')})
            self._set_transaction_pending()
            return True
        elif status_code in self._zift_cancel_tx_status:
            self.write({'acquirer_reference': data.get('BRQ_TRANSACTIONS')})
            self._set_transaction_cancel()
            return True
        else:
            error = 'Zift: feedback error'
            _logger.info(error)
            self.write({
                'state_message': error,
                'acquirer_reference': data.get('BRQ_TRANSACTIONS'),
            })
            self._set_transaction_cancel()
            return False
