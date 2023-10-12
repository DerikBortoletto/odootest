import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.production.lot'

    manufacture_date = fields.Datetime(string='Manufacturing Date',
        help='This is the date goods with this Serial Number were manufactured.')

    def _get_dates(self, product_id=None, type='expire'):
        """Returns dates based on number of days configured in current lot's product."""
        mapped_fields = {
            'expiration_date': 'expiration_time',
            'use_date': 'use_time',
            'removal_date': 'removal_time',
            'alert_date': 'alert_time'
        }
        res = dict.fromkeys(mapped_fields, False)
        product = self.env['product.product'].browse(product_id) or self.product_id
        if product:
            for field in mapped_fields:
                duration = getattr(product, mapped_fields[field])
                if duration:
                    date = datetime.datetime.now() + datetime.timedelta(days=duration)
                    res[field] = fields.Datetime.to_string(date)
        return res

    @api.onchange('manufacture_date')
    def _onchange_manufacture_date(self):
        if not self._origin or not bool(self.manufacture_date) or self.env.context.get('no_change_manufacture', False):
            return
        time_delta = datetime.timedelta(days = self.product_id.expiration_time or 0.0)
        vals = {'expiration_date': self.manufacture_date + time_delta}
        context = dict(self.env.context or {})
        context['no_change_manufacture'] = True
        self.with_context(context).update(vals)
        
    @api.onchange('expiration_date')
    def _onchange_expiration_date(self):
        if not self._origin or not (self.expiration_date and self._origin.expiration_date):
            return
        time_delta = self.expiration_date - self._origin.expiration_date
        time_delta_exp = datetime.timedelta(days = self.product_id.expiration_time or 0.0)
        # As we compare expiration_date with _origin.expiration_date, we need to
        # use `_get_date_values` with _origin to keep a stability in the values.
        # Otherwise it will recompute from the updated values if the user calls
        # this onchange multiple times without save between each onchange.
        vals = self._origin._get_date_values(time_delta, self.expiration_date)
        if not self.env.context.get('no_change_manufacture', False):
            vals['manufacture_date'] = self.expiration_date - time_delta_exp
        context = dict(self.env.context or {})
        context['no_change_manufacture'] = True
        self.with_context(context).update(vals)
