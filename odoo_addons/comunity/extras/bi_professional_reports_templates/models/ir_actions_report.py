# from odoo import models, api, _
# from odoo.exceptions import UserError
# from odoo.tools.float_utils import float_compare

# class IrActionsReport(models.Model):
#     _inherit = 'ir.actions.report'


#     def _render_qweb_pdf(self, res_ids, data):
#         if self.model == 'purchase.order':
#             if self.prescription_order:
#                 print_order = self.report_action()
#                 return (print_order, self.prescription_report())
#             if self.patient and self.prescription_order:
#                 return (
#                     self.patient.report_action(),
#                     self.prescription_report(),
#                     self.report_action()
#                 )
#             else:
#                 pass
        # Overridden so that the print > invoices actions raises an error
#         # when trying to print a miscellaneous operation instead of an invoice.
#         if self.model == 'sale.order' and res_ids:
#             response_ids = res_ids
#             pdf_data = data
            
#             sale_data = self.env['sale.order'].search_read([])
#             sale_order = self.env['sale.order'].search_read([('id', '=', res_ids)])
#             # doctor_ids = self.env['medical.physician'].search_read([])
#             res_company_data = self.env['res.company'].search_read([('id', '=', res_ids)])
            
#             pass
            
#         if self.model == 'purchase.order' and res_ids:
#             response_ids = res_ids
#             pdf_data = data
#             purchase_data = self.env['purchase.order'].search_read([])
#             purchase = self.env['purchase.order'].search_read([('id', '=', res_ids)])            
            
#             pass

#         return super()._render_qweb_pdf(res_ids=res_ids, data=data)
        # else:
        #     pass




    # def prescription_report(self):
    #     return self.env.ref('basic_hms.report_print_prescription').report_action(self)
#     def _get_rendering_context(self, docids, data):
#         data = data and dict(data) or {}
#         data.update({'float_compare': float_compare})
#         return super()._get_rendering_context(docids=docids, data=data)

#     def retrieve_attachment(self, record):
#         # get the original bills through the message_main_attachment_id field of the record
#         if self.report_name == 'sale.sale_report_templates' and record.message_main_attachment_id:
#             if record.message_main_attachment_id.mimetype == 'application/pdf' or \
#                record.message_main_attachment_id.mimetype.startswith('image'):
#                 return record.message_main_attachment_id
#         return super(IrActionsReport, self).retrieve_attachment(record)

#     def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
#         # don't include the generated dummy report
#         if self.report_name == 'sale.sale_report_templates':
#             pdf_content = None
#             res_ids = None
#             if not save_in_attachment:
#                 raise UserError(_("No original vendor bills could be found for any of the selected vendor bills."))
#         return super(IrActionsReport, self)._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=res_ids)

#     def _postprocess_pdf_report(self, record, buffer):
#         # don't save the 'account.report_original_vendor_bill' report as it's just a mean to print existing attachments
#         if self.report_name == 'sale.sale_report_templates':
#             return None
#         res = super(IrActionsReport, self)._postprocess_pdf_report(record, buffer)
#         if self.model == 'sale.order' and record.state == 'sale' and record.is_sale_document(include_receipts=True):
#             attachment = self.retrieve_attachment(record)
#             if attachment:
#                 attachment.register_as_main_attachment(force=False)
#         return res