from odoo import fields, models

class sale_order(models.Model):
    _inherit = 'sale.order'

    doctor_id = fields.Many2one('medical.physician','Physician')
    patient = fields.Many2one('medical.patient', string="Patient")
    prescription = fields.Many2one('medical.prescription.order', string='Prescription')

    # Doctor Data
    doctor_name = fields.Char(related="doctor_id.name", string='Doctor Name', readonly=True)
    doctor_code = fields.Char(related="doctor_id.code", string='CRM', readonly=True)
    doctor_specialty = fields.Char(related="doctor_id.medical_specialty", string='Medical Specialty', readonly=True)
    doctor_institution = fields.Char(related="doctor_id.institution", string='Adress', readonly=True)
    doctor_phone = fields.Char(related='doctor_id.phone', string='Phone', readonly=True)
    doctor_email = fields.Char(related='doctor_id.email', string='Email', readonly=True)
    doctor_city = fields.Char(related='doctor_id.city', string='City', readonly=True)
    doctor_state = fields.Many2one(related='doctor_id.state', string='State', readonly=True)
    doctor_country = fields.Many2one(related='doctor_id.country_code', string='Country', readonly=True)
    
    # Patient Data
    patient_name = fields.Char(related = 'patient.patient_id.name', readonly=True)
    patient_street = fields.Char(related = 'patient.patient_id.street', readonly=True)
    patient_city = fields.Char(related = 'patient.patient_id.city', readonly=True)
    patient_state = fields.Char(related = 'patient.patient_id.state_id.name', readonly=True)
    patient_country = fields.Char(related = 'patient.patient_id.country_id.name', readonly=True)
    patient_vat = fields.Char(related = 'patient.patient_id.vat', readonly=True)
    patient_zip = fields.Char(related = 'patient.patient_id.zip', readonly=True)
    
    # Prescription Data
    prescription_line = fields.One2many('medical.prescription.line', related='prescription.prescription_line_ids', readonly=True)
    
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env.ref('bi_professional_reports_templates.custom_report_sale_order').report_action(self)

    def write(self, vals):
        sale_data = self
        purchase_order_id = self.env['purchase.order'].search([('origin','=',self.name)])
        if len(purchase_order_id) < 2:
            if purchase_order_id.id:
                purchase_order_id.doctor_id = self.doctor_id
                purchase_order_id.patient = self.patient
                purchase_order_id.prescription = self.prescription
        else:
            if purchase_order_id[0].id:
                purchase_order_id.doctor_id = self.doctor_id
                purchase_order_id.patient = self.patient
                purchase_order_id.prescription = self.prescription

        return super(sale_order, self).write(vals)