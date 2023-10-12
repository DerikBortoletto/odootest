from odoo import fields, models

class account_invoice(models.Model):
    _inherit = "account.move"

    paypal_chk = fields.Boolean("Paypal")
    paypal_id = fields.Char("Paypal Id")
    patient_city = fields.Char()
    patient_country = fields.Char()
    patient_name = fields.Char()
    patient_state = fields.Char()
    patient_zip = fields.Char()
    patient_vat = fields.Char()
    patient_street = fields.Char()

    rename = fields.Float(compute='_rename')



    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env.ref('bi_professional_reports_templates.custom_account_invoices').report_action(self)

    def _rename(self):
        # info = self.env['purchase.order'].search_read([('id', '=', self.env.context.get('active_id'))])

        if self.invoice_filter_type_domain == 'sale':
            inf_2 = self.env['sale.order'].search([('id', '=', self.env.context.get('active_id'))])
            if len(inf_2) > 0:
                self.write(
                    {
                        'patient_city': inf_2.patient_city,
                        'patient_country': inf_2.patient_country,
                        'patient_name': inf_2.patient_name,
                        'patient_state': inf_2.patient_state,
                        'patient_zip': inf_2.patient_zip,
                        'patient_vat': inf_2.patient_vat,
                        'patient_street': inf_2.patient_street,
                    }
                )
        if self.invoice_filter_type_domain == 'purchase':
            inf_2 = self.env['purchase.order'].search([('id', '=', self.env.context.get('active_id'))])
            if len(inf_2) > 0:
                self.write(
                    {
                        'patient_city': inf_2.patient_city,
                        'patient_country': inf_2.patient_country,
                        'patient_name': inf_2.patient_name,
                        'patient_state': inf_2.patient_state,
                        'patient_zip': inf_2.patient_zip,
                        'patient_vat': inf_2.patient_vat,
                        'patient_street': inf_2.patient_street,
                    }
                )
        self.rename = 0.0


