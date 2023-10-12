# coding: utf-8
from werkzeug import urls

from .zift_request import ZiftAPI
import hashlib
import hmac
import logging
import time

from odoo import _, api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_zift.controllers.main import ZiftController
from odoo.tools.float_utils import float_compare, float_repr
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PaymentAcquirerZift(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('', 'Zift')
    ], ondelete={'': 'set default'})
    _user = fields.Char(string='API User Id', required_if_provider='', groups='base.group_user')
    _client_pass = fields.Char(string='API Client Pass', groups='base.group_user')
    _zift_signature_key = (string='API User Id', required_if_provider='', groups='base.group_user')
    _url_Base = fields.Char(string='API url Base', required_if_provider='', groups='base.group_user')

    @api.onchange('provider', 'check_validity')
    def onchange_check_validity(self):
        if self.provider == '' and self.check_validity:
            self.check_validity = False
            return {'warning': {
                'title': _("Warning"),
                'message': ('This option is not supported for Zift')}}

    def action_client_secret(self):
        api = ZiftAPI(self)
        if not api.test_authenticate():
            raise UserError(_('Unable to fetch Client Key, make sure the API Login and Transaction Key are correct.'))
        self.zift_user = api.get_client_pass()
        return True

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(PaymentAcquirerZift(pool, cr), self)._get_feature_support()
        res['zift'].append('zift')
        res['tokenize'].append('zift')
        return res

    def _get_zift_urls(self, environment):
        """ Zift URLs """
        if environment == 'prod':
            return {'zift_form_url': ' https://sandbox-secure.zift.io/gates/xurl'}
        else:
            return {'zift_form_url': ' https://sandbox-secure.zift.io/gates/xurl'}

    def _zift_generate_hashing(self, values):
        data = '^'.join([
            values['x_login'],
            values['x_fp_sequence'],
            values['x_fp_timestamp'],
            values['x_amount'],
            values['x_currency_code']]).encode('utf-8')

        return hmac.new(bytes.fromhex(self.zift_signature_key), data, hashlib.sha512).hexdigest().upper()

    def zift_form_generate_values(self, values):
        self.ensure_one()
        # State code is only supported in US, use state name by default
        # See https://developer.zift/api/reference/
        state = values['partner_state'].name if values.get('partner_state') else ''
        if values.get('partner_country') and values.get('partner_country') == self.env.ref('base.us', False):
            state = values['partner_state'].code if values.get('partner_state') else ''
        billing_state = values['billing_partner_state'].name if values.get('billing_partner_state') else ''
        if values.get('billing_partner_country') and values.get('billing_partner_country') == self.env.ref('base.us', False):
            billing_state = values['billing_partner_state'].code if values.get('billing_partner_state') else ''

        base_url = self.get_base_url()
        authorize_tx_values = dict(values)
        temp_zift_tx_values = {
            'x_login': self.zift_user,
            'x_amount': float_repr(values['amount'], values['currency'].decimal_places if values['currency'] else 2),
            'x_show_form': 'PAYMENT_FORM',
            'x_type': 'AUTH_CAPTURE' if not self.capture_manually else 'AUTH_ONLY',
            'x_method': 'CC',
            'x_fp_sequence': '%s%s' % (self.id, int(time.time())),
            'x_version': '3.1',
            'x_relay_response': 'TRUE',
            'x_fp_timestamp': str(int(time.time())),
            'x_relay_url': urls.url_join(base_url, ZiftController._return_url),
            'x_cancel_url': urls.url_join(base_url, ZiftController._cancel_url),
            'x_currency_code': values['currency'] and values['currency'].name or '',
            'address': values.get('partner_address'),
            'city': values.get('partner_city'),
            'country': values.get('partner_country') and values.get('partner_country').name or '',
            'email': values.get('partner_email'),
            'zip_code': values.get('partner_zip'),
            'first_name': values.get('partner_first_name'),
            'last_name': values.get('partner_last_name'),
            'phone': values.get('partner_phone'),
            'state': state,
            'billing_address': values.get('billing_partner_address'),
            'billing_city': values.get('billing_partner_city'),
            'billing_country': values.get('billing_partner_country') and values.get('billing_partner_country').name or '',
            'billing_email': values.get('billing_partner_email'),
            'billing_zip_code': values.get('billing_partner_zip'),
            'billing_first_name': values.get('billing_partner_first_name'),
            'billing_last_name': values.get('billing_partner_last_name'),
            'billing_phone': values.get('billing_partner_phone'),
            'billing_state': billing_state,
        }
        temp_zift_tx_values['returndata'] = zift_tx_values.pop('return_url', '')
        temp_zift_tx_values['x_fp_hash'] = self._zift_generate_hashing(temp_zift_tx_values)
        zift_tx_values.update(temp_zift_tx_values)
        return zift_tx_values

    def zift_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_zift_urls(environment)['zift_form_url']

    @api.model
    def zift_s2s_form_process(self, data):
        values = {
            'opaqueData': data.get('opaqueData'),
            'encryptedCardData': data.get('encryptedCardData'),
            'acquirer_id': int(data.get('acquirer_id')),
            'partner_id': int(data.get('partner_id'))
        }
        PaymentMethod = self.env['payment.token'].sudo().create(values)
        return PaymentMethod

    def zift_s2s_form_validate(self, data):
        error = dict()
        mandatory_fields = ["opaqueData", "encryptedCardData"]
        # Validation
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'
        return False if error else True

    def zift_test_credentials(self):
        self.ensure_one()
        transaction = ZiftAPI(self.acquirer_id)
        return transaction.test_authenticate()

class TxZift(models.Model):
    _inherit = 'payment.transaction'

    _zift_valid_tx_status = 1
    _zift_pending_tx_status = 4
    _zift_cancel_tx_status = 2
    _zift_error_tx_status = 3

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _zift_form_get_tx_from_data(self, data):
        """ Given a data dict coming from zift, verify it and find the related
        transaction record. """
        reference, description, trans_id, fingerprint = data.get('x_invoice_num'), data.get('x_description'), data.get('x_trans_id'), data.get('x_SHA2_Hash') or data.get('x_MD5_Hash')
        if not reference or not trans_id or not fingerprint:
            error_msg = _('Zift: received data with missing reference (%s) or trans_id (%s) or fingerprint (%s)') % (reference, trans_id, fingerprint)
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        tx = self.search(['|', ('reference', '=', reference), ('reference', '=', description)])
        if not tx or len(tx) > 1:
            error_msg = 'Zift: received data for x_invoice_num %s and x_description %s' % (reference, description)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return tx[0]

    def _zift_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if self.acquirer_reference and data.get('x_trans_id') != self.acquirer_reference:
            invalid_parameters.append(('Transaction Id', data.get('x_trans_id'), self.acquirer_reference))
        # check what is buyed
        if float_compare(float(data.get('x_amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('Amount', data.get('x_amount'), '%.2f' % self.amount))
        return invalid_parameters

    def _zift_form_validate(self, data):
        if self.state == 'done':
            _logger.warning('Zift: trying to validate an already validated tx (ref %s)' % self.reference)
            return True
        status_code = int(data.get('x_response_code', '0'))
        if status_code == self._zift_valid_tx_status:
            if data.get('x_type').lower() in ['auth_capture', 'prior_auth_capture']:
                self.write({
                    'acquirer_reference': data.get('x_trans_id'),
                    'date': fields.Datetime.now(),
                })
                self._set_transaction_done()
            elif data.get('x_type').lower() in ['auth_only']:
                self.write({'acquirer_reference': data.get('x_trans_id')})
                self._set_transaction_authorized()
            if self.partner_id and not self.payment_token_id and \
               (self.type == 'form_save' or self.acquirer_id.save_token == 'always'):
                transaction = ZiftAPI(self.acquirer_id)
                res = transaction.create_customer_profile_from_tx(self.partner_id, self.acquirer_reference)
                if res:
                    token_id = self.env['payment.token'].create({
                        'zift_profile': res.get('profile_id'),
                        'name': res.get('name'),
                        'acquirer_ref': res.get('payment_profile_id'),
                        'acquirer_id': self.acquirer_id.id,
                        'partner_id': self.partner_id.id,
                    })
                    self.payment_token_id = token_id
            return True
        elif status_code == self._zift_pending_tx_status:
            self.write({'acquirer_reference': data.get('x_trans_id')})
            self._set_transaction_pending()
            return True
        else:
            error = data.get('x_response_reason_text')
            _logger.info(error)
            self.write({
                'state_message': error,
                'acquirer_reference': data.get('x_trans_id'),
            })
            self._set_transaction_cancel()
            return False

    def zift_s2s_do_transaction(self, **data):
        self.ensure_one()
        transaction = ZiftAPI(self.acquirer_id)

        if not self.payment_token_id.zift_profile:
            raise UserError(_('Invalid token found: the Authorize profile is missing.'
                              'Please make sure the token has a valid acquirer reference.'))

        if not self.acquirer_id.capture_manually:
            res = transaction.auth_and_capture(self.payment_token_id, round(self.amount, self.currency_id.decimal_places), self.reference)
        else:
            res = transaction.zift(self.payment_token_id, round(self.amount, self.currency_id.decimal_places), self.reference)
        return self._zift_s2s_validate_tree(res)

    def zift_s2s_capture_transaction(self):
        self.ensure_one()
        transaction = ZiftAPI(self.acquirer_id)
        tree = transaction.capture(self.acquirer_reference or '', round(self.amount, self.currency_id.decimal_places))
        return self._zift_s2s_validate_tree(tree)

    def zift_s2s_void_transaction(self):
        self.ensure_one()
        transaction = ZiftAPI(self.acquirer_id)
        tree = transaction.void(self.acquirer_reference or '')
        return self._zift_s2s_validate_tree(tree)

    def _zift_s2s_validate_tree(self, tree):
        return self._zift_s2s_validate(tree)

    def _zift_s2s_validate(self, tree):
        if self.state == 'done':
            _logger.warning('Zift: trying to validate an already validated tx (ref %s)' % self.reference)
            return True
        status_code = int(tree.get('x_response_code', '0'))
        if status_code == self._zift_valid_tx_status:
            if tree.get('x_type').lower() in ['auth_capture', 'prior_auth_capture']:
                init_state = self.state
                self.write({
                    'acquirer_reference': tree.get('x_trans_id'),
                    'date': fields.Datetime.now(),
                })

                self._set_transaction_done()

                if init_state != 'authorized':
                    self.execute_callback()
            if tree.get('x_type').lower() == 'auth_only':
                self.write({'acquirer_reference': tree.get('x_trans_id')})
                self._set_transaction_authorized()
                self.execute_callback()
            if tree.get('x_type').lower() == 'void':
                self._set_transaction_cancel()
            return True
        elif status_code == self._zift_pending_tx_status:
            self.write({'acquirer_reference': tree.get('x_trans_id')})
            self._set_transaction_pending()
            return True
        else:
            error = tree.get('x_response_reason_text')
            _logger.info(error)
            self.write({
                'acquirer_reference': tree.get('x_trans_id'),
            })
            self._set_transaction_error(msg=error)
            return False


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    zift_profile = fields.Char(string='Authorize.net Profile ID', help='This contains the unique reference '
                                    'for this partner/payment token combination in the Zift backend')
    provider = fields.Selection(string='Provider', related='acquirer_id.provider', readonly=False)
    save_token = fields.Selection(string='Save Cards', related='acquirer_id.save_token', readonly=False)

    @api.model
    def ziftcreate(self, values):
        if values.get('opaqueData') and values.get('encryptedCardData'):
            acquirer = self.env['payment.acquirer'].browse(values['acquirer_id'])
            partner = self.env['res.partner'].browse(values['partner_id'])
            transaction = ZiftAPI(acquirer)
            res = transaction.create_customer_profile(partner, values['opaqueData'])
            if res.get('profile_id') and res.get('payment_profile_id'):
                return {
                    'authorize_profile': res.get('profile_id'),
                    'name': values['encryptedCardData'].get('cardNumber'),
                    'acquirer_ref': res.get('payment_profile_id'),
                    'verified': True
                }
            else:
                raise ValidationError(_('The Customer Profile creation in Zift failed.'))
        else:
            return values
