from odoo import fields, models

class CopyOutboundShipmentToCustom2ndParty(models.Model):
    _name = 'copy.outbound.shipment.to.custom.2nd.party'
    _description = 'copy_outbound_shipment_to_custom_2nd_party'

    # TTR2 Fields
    # This model will receive the Outbound Shipment Copy to Custom 2nd Party
    # vinculated to the product
    # Create Right Access to model into ir.access.csv
    uuid = fields.Char("UUID", copy=False)
    created_on = fields.Datetime('Create On', readonly=True)
    type = fields.Char('2nd Party Type')
    last_update = fields.Datetime('Last Update', readonly=True)
    name = fields.Char(
        string="Name"
    )
    gs1_id = fields.Char("GS1 ID", required=True)
    gs1_company_id = fields.Char("GS 1 COMPANY ID", required=True)
    gs1_sgln = fields.Char("GS 1 SGLN", required=True)
    sender_id = fields.Char("Sender ID for X12 EDI", required=True)
    receiver_id = fields.Char("Override Receiver ID for X12 EDI", required=True)
    as2_id = fields.Char("AS2ID", required=True)
    
    serial_id = fields.Char('SERIAL ID', required=True)