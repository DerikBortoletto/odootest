# Copyright 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from datetime import datetime
from email.utils import COMMASPACE

from odoo import fields, models


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _tracking_email_prepare(self, partner, email):
        """Prepare email.tracking.email record values"""
        ts = time.time()
        dt = datetime.utcfromtimestamp(ts)
        email_to_list = email.get("email_to", [])
        email_to = COMMASPACE.join(email_to_list)
        return {
            "name": self.subject,
            "timestamp": "%.6f" % ts,
            "time": fields.Datetime.to_string(dt),
            "mail_id": self.id,
            "mail_message_id": self.mail_message_id.id,
            "partner_id": partner.id if partner else False,
            "recipient": email_to,
            "sender": self.email_from,
        }

    def _send_prepare_values(self, partner=None):
        """Creates the mail.tracking.email record and adds the image tracking
        to the email"""
        email = super()._send_prepare_values(partner=partner)
        vals = self._tracking_email_prepare(partner, email)
        tracking_email = self.env["mail.tracking.email"].sudo().create(vals)
        return tracking_email.tracking_img_add(email)

    def _postprocess_sent_message(self, success_pids, failure_reason=False, failure_type=None):
        notif_mails_ids = [mail.id for mail in self if mail.notification]
        if notif_mails_ids:
            notifications = self.env['mail.notification'].search([
                ('notification_type', '=', 'email'),
                ('mail_id', 'in', notif_mails_ids),
                ('notification_status', 'not in', ('sent', 'canceled'))
            ])
            if notifications:
                # find all notification linked to a failure
                failed = self.env['mail.notification']
                if failure_type:
                    failed = notifications.filtered(lambda notif: notif.res_partner_id not in success_pids)
                (notifications - failed).sudo().write({
                    'notification_status': 'sent',
                    'failure_type': '',
                    'failure_reason': '',
                })
                if failed:
                    failed.sudo().write({
                        'notification_status': 'exception',
                        'failure_type': failure_type,
                        'failure_reason': failure_reason,
                    })
                    messages = notifications.mapped('mail_message_id').filtered(lambda m: m.is_thread_message())
                    # TDE TODO: could be great to notify message-based, not notifications-based, to lessen number of notifs
                    messages._notify_message_notification_update()  # notify user that we have a failure
        # if not failure_type or failure_type == 'RECIPIENT':  # if we have another error, we want to keep the mail.
        #     mail_to_delete_ids = [mail.id for mail in self if mail.auto_delete]
        #     self.browse(mail_to_delete_ids).sudo().unlink()
        return True
