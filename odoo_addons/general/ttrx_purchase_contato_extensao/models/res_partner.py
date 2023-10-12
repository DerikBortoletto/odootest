# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _

class Partner(models.Model):
    _inherit = 'res.partner'


    fornecedor = fields.Boolean(string="Fornecedor", default=False)


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'