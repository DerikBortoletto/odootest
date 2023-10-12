
from hashlib import sha1
import logging

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError


from odoo.tools.float_utils import float_compare
import urllib.parse
import urllib.request

class ViewFront(models.Model):
    _name = "view_front"
    _description = "View Front"

    name = fields.Char()
    amount = fields.Char()
    id_da_venda = fields.Char()
    usuario = fields.Char()
    data = fields.Char()
    produto = fields.Char()
    dicionario = fields.Char()




