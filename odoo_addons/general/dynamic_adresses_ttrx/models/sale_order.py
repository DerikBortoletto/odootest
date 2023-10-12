from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    patient_name = fields.Char(related='patient.patient_id.name', readonly=True, store="True")
    patient_street = fields.Char(related='patient.patient_id.street', readonly=True, store="True")
    patient_city = fields.Char(related='patient.patient_id.city', readonly=True, store="True")
    patient_state = fields.Char(related='patient.patient_id.state_id.name', readonly=True, store="True")
    patient_country = fields.Char(related='patient.patient_id.country_id.name', readonly=True, store="True")
    patient_vat = fields.Char(related='patient.patient_id.vat', readonly=True, store="True")
    patient_zip = fields.Char(related='patient.patient_id.zip', readonly=True, store="True")


    different_adress = fields.Boolean(string = 'Choose different address?')
    
    search_address_id = fields.Many2one(
        comodel_name = "res.partner",
        inverse_name = 'childs_ids',
        string = "Choose Patient Delivery Address",
    )

    numero = fields.Integer(default=0)

    def next_address(self):
        if not self.patient.patient_id.child_ids :
            self.update({
                'search_address_id': False
            })
        elif len(self.patient.patient_id.child_ids) > self.numero:
            self.update({
                'search_address_id': self.patient.patient_id.child_ids[self.numero],
            })
            self.update({
                'patient_name': self.patient.patient_id.child_ids[self.numero].name,
                'patient_street': self.patient.patient_id.child_ids[self.numero].street,
                'patient_city': self.patient.patient_id.child_ids[self.numero].city,
                'patient_state': self.patient.patient_id.child_ids[self.numero].state_id.name,
                'patient_country': self.patient.patient_id.child_ids[self.numero].country_id.name,
                'patient_zip': self.patient.patient_id.child_ids[self.numero].zip,
                'patient_vat': self.patient.patient_id.child_ids[self.numero].vat,
            })
            self.write({
                'numero': self.numero + 1,
            })

        else:
            self.write({
                'numero': 0,
            })
            self.update({
                'search_address_id': self.patient.patient_id.child_ids[0]
            })

        pass


