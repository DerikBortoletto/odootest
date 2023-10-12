import re
import logging
import base64
from datetime import datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except ImportError:
    _logger.error('Cannot import OpenSSL.crypto', exc_info=True)

CERT_STATE = [
    ('not_loaded', 'Not loaded'),
    ('expired', 'Expired'),
    ('invalid_password', 'Invalid Password'),
    ('unknown', 'Unknown'),
    ('valid', 'Valid')
]

class ResCompany(models.Model):
    _inherit = 'res.company'

    def _compute_expiry_date(self):
        for company in self:
            company.cert_state = 'unknown'
            company.cert_expire_date = False
            company.cert_information = False
            try:
                if company.with_context(bin_size=False).nfe_a1_file:
                    pfx = base64.decodestring(company.with_context(bin_size=False).nfe_a1_file)
                    pfx = crypto.load_pkcs12(pfx, company.nfe_a1_password)
                    cert = pfx.get_certificate()
                    end = datetime.strptime(cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
                    subj = cert.get_subject()
                    company.cert_expire_date = end
                    if datetime.now() < end:
                        company.cert_state = 'valid'
                    else:
                        company.cert_state = 'expired'
                    company.cert_information = "%s\n%s\n%s\n%s" % (subj.CN, subj.L, subj.O, subj.OU)
            except crypto.Error:
                company.cert_state = 'invalid_password'
            except:
                company.cert_state = 'unknown'
                _logger.warning(_('Unknown error when validating certificate'), exc_info=True)

    nfe_a1_file = fields.Binary('NFe A1 File')
    nfe_a1_password = fields.Char('NFe A1 Password', size=64)
    cert_state = fields.Selection(CERT_STATE, string="Cert. State", compute=_compute_expiry_date, default='not_loaded')
    cert_information = fields.Text(string="Cert. Info", compute=_compute_expiry_date)
    cert_expire_date = fields.Date(string="Cert. Expiration Date", compute=_compute_expiry_date)
    ibpt_api_token = fields.Char(string="IBPT Api Token", size=200)

