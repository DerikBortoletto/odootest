from odoo import fields, models, api

class CustomReport(models.AbstractModel):
    _name = 'report.sale.order'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('bi_professional_reports_templates.custom_report_sale_order')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self
        }

        return report_obj.render('bi_professional_reports_templates.custom_report_sale_order', docargs)