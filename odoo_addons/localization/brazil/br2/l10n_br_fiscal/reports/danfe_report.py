import pytz
import base64
import logging
from lxml import etree
from io import BytesIO
from odoo import models

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe.danfe import danfe
    from pytrustnfe.nfe.danfce import danfce
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_html(self, res_ids, data=None):
        if self.report_name == 'l10n_br_fiscal.main_template_br_nfe_danfe':
            return

        return super(IrActionsReport, self)._render_qweb_html(res_ids, data=data)

    def _render_qweb_pdf(self, res_ids, data=None):
        if self.report_name != 'l10n_br_fiscal.main_template_br_nfe_danfe':
            return super(IrActionsReport, self)._render_qweb_pdf(res_ids, data=data)

        nfe = self.env['l10n_br_fiscal.document'].search([('id', 'in', res_ids)])

        nfe_xml = base64.decodebytes(nfe.authorization_file_id.datas or nfe.send_file_id.datas).decode('utf-8')

        cce_xml_element = []
        # cce_list = self.env['ir.attachment'].search([
        #     ('res_model', '=', 'eletronic.document'),
        #     ('res_id', '=', nfe.id),
        #     ('name', 'like', 'cce-')
        # ])
        #
        # if cce_list:
        #     for cce in cce_list:
        #         cce_xml = base64.decodestring(cce.datas)
        #         cce_xml_element.append(etree.fromstring(cce_xml))

        logo = False

        if bool(nfe.company_id.logo):
            logo = base64.decodestring(nfe.company_id.logo)
        elif bool(nfe.company_id.logo_web):
            logo = base64.decodestring(nfe.company_id.logo_web)

        if logo:
            tmpLogo = BytesIO()
            tmpLogo.write(logo)
            tmpLogo.seek(0)
        else:
            tmpLogo = False

        timezone = pytz.timezone(self.env.context.get('tz') or 'UTC')

        xml_element = etree.fromstring(nfe_xml)
        if nfe.document_type_id.code == '65':
            oDanfe = danfce(list_xml=[xml_element], logo=tmpLogo, timezone=timezone)
        elif nfe.document_type_id.code == '55':
            oDanfe = danfe(list_xml=[xml_element], logo=tmpLogo, cce_xml=cce_xml_element, timezone=timezone)

        tmpDanfe = BytesIO()
        oDanfe.writeto_pdf(tmpDanfe)
        danfe_file = tmpDanfe.getvalue()
        tmpDanfe.close()

        return danfe_file, 'pdf'
