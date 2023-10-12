import logging

from odoo import models, fields, api
from ..tools import CleanDataDict, DateTimeToOdoo


_logger = logging.getLogger(__name__)


class product_lot_spt(models.Model): #TODO: Rever
    _name = 'product.lot.spt'
    _inherit = "custom.connector.spt"
    _description = 'Product Lots'
    _inherits = {'stock.production.lot': 'product_id'}
    _TTRxKey = 'lot_number'
    _OdooToTTRx = {'uuid':'product_uuid'}
    _TTRxToOdoo = {'uuid':'uuid'}
    # _rec_name = 'address_nickname'


    production_lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial', ondelete='cascade') # Lot Linked

    # TTRx2 Fields
    product_uuid = fields.Char(string="Product UUID", readonly=True, copy=False)
    manufacturer_id = fields.Many2one('manufacturers.spt', 'Manufacturer')
    # lot_number = name
    # new_lot_number = name *** Usado na criação
    # production_date =
    # best_by_date = use_date
    # sell_by_date = life_date
    # expiration_date = removal_date
    
    @api.onchange('product_uuid')
    def on_change_account_range(self):
        product_spt = self.env['product.spt'].search([('uuid','=',self.product_uuid)],limit=1)
        self.product_id = product_spt.product_id

    def FromOdooToTTRx(self, connector, values={}):
        var = super().FromOdooToTTRx(connector=connector,values=values)
        if bool(values):
            lot_number = None
            new_lot_number = self.name
        else:
            lot_number = self.name
            new_lot_number = None


        var.update({
            'product_uuid': values.get('product_uuid',self.product_uuid if bool(self.product_uuid) else None),
            'lot_number': lot_number,
            'new_lot_number': new_lot_number,
            'production_date': None,
            'best_by_date': values.get('use_date', self.use_date),
            'sell_by_date': values.get('life_date', self.life_date),
            'expiration_date': values.get('removal_date', self.removal_date),
        })
        CleanDataDict(var)
        return var

    def FromTTRxToOdoo(self, connector, values):
        var = super().FromTTRxToOdoo(connector, values)
        # print("Product Lot SPT ", values)
        var.update({
            'product_uuid': values('product_uuid'),
            'name': values('lot'),
            'production_date': None,
            'use_date': DateTimeToOdoo(values.get('best_by_date')),
            'life_date': DateTimeToOdoo(values.get('sell_by_date')),
            'removal_date': DateTimeToOdoo(values.get('expiration_date')),
        })
        CleanDataDict(var)
        return var

    def action_send(self):
        for reg in self:
            reg.CreateInTTRx()
        return True

    def action_test(self):
        # 'location': {'location_uuid': 'location_uuid', 'tt_id': 'id'}
        self.SyncFromTTRx(self.connector_id,location_uuid='cb251f49-3276-41a6-9bda-eda4225b5811',primary_model='location')
        return True


