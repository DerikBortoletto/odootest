import logging
import re
from odoo import api, fields, models, _
logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def convert_email_from_to_email(self, str1):
        result = re.search('<(.*)>', str1)
        return result.group(1)
