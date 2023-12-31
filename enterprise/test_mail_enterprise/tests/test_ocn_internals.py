# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.mail.tests.common import MailCommon, mail_new_test_user
from odoo.tests import tagged
from unittest.mock import patch


@tagged('post_install', '-at_install')
class TestPushNotification(MailCommon):

    @classmethod
    def setUpClass(cls):
        super(TestPushNotification, cls).setUpClass()
        sudo_icp = cls.env['ir.config_parameter'].sudo()
        sudo_icp.set_param('odoo_ocn.project_id', 'Test')
        sudo_icp.set_param('mail_mobile.enable_ocn', True)

        channel = cls.env['mail.channel'].with_context(cls._test_context)

        cls.user_email = cls.user_employee
        cls.user_email.notification_type = 'email'
        cls.user_email.partner_id.ocn_token = 'Test OCN Email'

        cls.user_inbox = mail_new_test_user(
            cls.env, login='user_inbox', groups='base.group_user', name='User Inbox',
            notification_type='inbox'
        )
        cls.user_inbox.partner_id.ocn_token = 'Test OCN Inbox'

        cls.record_simple = cls.env['mail.test.simple'].with_context(cls._test_context).create({
            'name': 'Test',
            'email_from': 'ignasse@example.com'
        })
        cls.record_simple.message_subscribe(partner_ids=[
            cls.user_email.partner_id.id,
            cls.user_inbox.partner_id.id,
        ])

        cls.direct_message_channel = channel.create({
            'channel_partner_ids': [
                (4, cls.user_email.partner_id.id),
                (4, cls.user_inbox.partner_id.id),
            ],
            'public': 'private',
            'channel_type': 'chat',
            'email_send': False,
            'name': "Direct Message",
        })

        cls.group_channel = channel.create({
            'channel_partner_ids': [
                (4, cls.user_email.partner_id.id),
                (4, cls.user_inbox.partner_id.id),
            ],
            'public': 'public',
            'email_send': False,
            'name': 'Channel',
        })
        cls.group_channel.message_subscribe(
            partner_ids=[
                cls.user_email.partner_id.id,
                cls.user_inbox.partner_id.id,
            ]
        )

    @patch('odoo.addons.mail_mobile.models.mail_thread.iap_tools.iap_jsonrpc')
    def test_push_notifications(self, jsonrpc):
        # Test No Inbox Condition
        self.record_simple.with_user(self.user_inbox).message_notify(
            partner_ids=self.user_email.partner_id.ids,
            body="Test",
            subject="Test Activity",
            record_name=self.record_simple._name,
        )
        jsonrpc.assert_not_called()

        self.record_simple.with_user(self.user_email).message_notify(
            partner_ids=self.user_inbox.partner_id.ids,
            body="Test message send via OCN",
            subject="Test Activity",
            record_name=self.record_simple._name,
        )
        jsonrpc.assert_called_once()
        self.assertEqual(jsonrpc.call_args[1]['params']['data']['model'], 'mail.test.simple')
        self.assertEqual(jsonrpc.call_args[1]['params']['data']['res_id'], self.record_simple.id)
        self.assertEqual(jsonrpc.call_args[1]['params']['data']['author_name'], self.user_email.name)
        self.assertIn(
            "Test message send via OCN",
            jsonrpc.call_args[1]['params']['data']['body'],
            'The body must be "Test message send via OCN"'
        )

        # Reset the mock counter
        jsonrpc.reset_mock()

        # Test Tracking Message
        mail_test_ticket = self.env['mail.test.ticket'].with_context(self._test_context)
        record_full = mail_test_ticket.with_user(self.user_email).create({
            'name': 'Test',
        })
        record_full = record_full.with_context(mail_notrack=False)

        container = self.env['mail.test.container'].create({'name': 'Container'})
        record_full.message_subscribe(
            partner_ids=[self.user_email.partner_id.id],
            subtype_ids=[self.env.ref('test_mail.st_mail_test_ticket_container_upd').id],
        )
        record_full.write({
            'name': 'Test2',
            'email_from': 'noone@example.com',
            'container_id': container.id,
        })
        self.flush_tracking()
        jsonrpc.assert_not_called()

        container2 = self.env['mail.test.container'].create({'name': 'Container Two'})
        record_full.message_subscribe(
            partner_ids=[self.user_inbox.partner_id.id],
            subtype_ids=[self.env.ref('test_mail.st_mail_test_ticket_container_upd').id],
        )
        record_full.write({
            'name': 'Test3',
            'email_from': 'noone@example.com',
            'container_id': container2.id,
        })
        self.flush_tracking()
        jsonrpc.assert_called_once()
        # As the tracking values are converted to text. We check the '→' added by ocn_client.
        self.assertIn(
            '→',
            jsonrpc.call_args[1]['params']['data']['body'],
            'No Tracking Message found'
        )

    @patch('odoo.addons.mail_mobile.models.mail_thread.iap_tools.iap_jsonrpc')
    def test_push_notifications_android_channel(self, jsonrpc):
        # Test Direct Message
        self.direct_message_channel.with_user(self.user_email).message_post(
            body="Test", message_type='comment', subtype_xmlid='mail.mt_comment')
        self.assertEqual(
            jsonrpc.call_args[1]['params']['data']['android_channel_id'],
            'DirectMessage',
            'The type of Android channel must be DirectMessage'
        )

        # Reset the mock counter
        jsonrpc.reset_mock()

        # Test Channel Message
        self.group_channel.with_user(self.user_email).message_post(
            body="Test", message_type='comment', subtype_xmlid='mail.mt_comment')
        self.assertEqual(
            jsonrpc.call_args[1]['params']['data']['android_channel_id'],
            'ChannelMessage',
            'The type of Android channel must be ChannelMessage'
        )

        # Reset the mock counter
        jsonrpc.reset_mock()

        # Test Following Message
        self.record_simple.with_user(self.user_email).message_post(
            body="Test", message_type='comment', subtype_xmlid="mail.mt_comment"
        )
        self.assertEqual(
            jsonrpc.call_args[1]['params']['data']['android_channel_id'],
            'Following',
            'The type of Android channel must be Following'
        )

        # Reset the mock counter
        jsonrpc.reset_mock()

        # Test AtMention Message
        self.record_simple.with_user(self.user_email).message_post(
            body='<a href="/web" data-oe-id="%i" data-oe-model="res.partner" >@user</a>' %
                 self.user_inbox.partner_id.id,
            message_type='comment', subtype_xmlid="mail.mt_comment"
        )
        self.assertEqual(
            jsonrpc.call_args[1]['params']['data']['android_channel_id'],
            'AtMention',
            'The type of Android channel must be AtMention'
        )

    @patch('odoo.addons.mail_mobile.models.mail_thread.iap_tools.iap_jsonrpc')
    def test_push_notifications_binary_body(self, jsonrpc):
        template = self.env['ir.ui.view'].create({
            'name': "dummy",
            'type': 'qweb',
            'arch': u"""
                <p>Test</p>
            """
        })
        kwargs = {
            'body': template._render(),
            'partner_ids': self.user_inbox.partner_id.ids,
            'msg_type': 'user_notification'
        }
        # Here is the test: notifying user with template rendered from an 'ir.ui.view'
        # should not raised an error an when searching model and res_id in body with regex
        self.env['mail.thread'].with_context(mail_notify_author=True).message_notify(**kwargs)
        jsonrpc.assert_called_once()
