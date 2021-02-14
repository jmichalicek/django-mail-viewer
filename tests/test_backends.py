"""
Test django_mail_viewer.backends
"""
from __future__ import absolute_import, division, unicode_literals

import json
import shutil
from pathlib import Path

from django.conf import settings
from django.core import cache, mail
from django.test import SimpleTestCase, TestCase

from django_mail_viewer.backends.database.models import EmailMessage


class LocMemBackendTest(SimpleTestCase):
    """
    Test django_mail_viewer.backends.locmem.EmailBackend
    """
    # TODO: test_get_outbox()

    def setUp(self):
        mail.outbox = []

    def test_send_messages_adds_message_to_mail_outbox(self):
        """
        send_messages() method should append the sent email.Message to mail.outbox
        """

        m = mail.EmailMultiAlternatives(
            'Email 2 subject', 'Email 2 text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            self.assertEqual([], mail.outbox)
            self.assertEqual(1, connection.send_messages([m]))
            self.assertEqual(1, len(mail.outbox))

    def test_get_message_returns_requested_message(self):

        m = mail.EmailMultiAlternatives(
            'Email 2 subject', 'Email 2 text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        m2 = mail.EmailMultiAlternatives(
            'Email 2 subject', 'Email 2 text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )

        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            connection.send_messages([m, m2])
            self.assertEqual(2, len(mail.outbox))
            for message in mail.outbox:
                # check that we can use the message id to look up a specific message's data
                self.assertEqual(message, connection.get_message(message.get('Message-ID')))


class CacheBackendTest(SimpleTestCase):
    """
    Test django_mail_viewer.backends.cache.EmailBackend
    """
    # TODO: test_get_message()
    # TODO: test_get_outbox()

    def setUp(self):
        # not sure this is the best way to do this, but it'll work for now
        self.mail_cache = cache.caches[settings.MAILVIEWER_CACHE]
        self.mail_cache.clear()

    def test_send_messages_adds_message_to_cache(self):
        m = mail.EmailMultiAlternatives(
            'Email 2 subject', 'Email 2 text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        with mail.get_connection('django_mail_viewer.backends.cache.EmailBackend') as connection:
            self.mail_cache.delete(connection.cache_keys_key)
            self.assertIsNone(self.mail_cache.get(connection.get_outbox()))
            self.assertEqual(1, connection.send_messages([m]))
            self.assertEqual(1, len(self.mail_cache.get(connection.cache_keys_key)))


class DatabaseBackendTest(TestCase):
    """
    Test django_mail_viewer.backends.cache.EmailBackend
    """

    # TODO: test_get_message()
    # TODO: test_get_outbox()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            media_dir = Path(settings.MEDIA_ROOT)
            shutil.rmtree(media_dir)
        finally:
            super().tearDownClass()

    def test_send_plaintext_email(self):
        original_email_count = EmailMessage.objects.count()
        m = mail.EmailMultiAlternatives(
            'Email subject', 'Email text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        with mail.get_connection('django_mail_viewer.backends.database.backend.EmailBackend') as connection:
            self.assertEqual(1, connection.send_messages([m]))

        self.assertEqual(original_email_count + 1, EmailMessage.objects.count())
        email = EmailMessage.objects.latest('id')

        expected_headers = {
            "Content-Type": "text/plain; charset=\"utf-8\"",
            "MIME-Version": "1.0",
            "Content-Transfer-Encoding": "7bit",
            "Subject": "Email subject",
            "From": "test@example.com",
            "To": "to1@example.com, to2.example.com",
            "Message-ID": email.message_id,
        }
        actual_headers = json.loads(email.message_headers)
        # Make sure there is a `Date` key in the headers and it has a value, but am not trying to match it up since
        # I have no good way of knowing what it should be.
        self.assertTrue(actual_headers.get('Date'))
        # Now remove the `Date` key so that the dicts can be compared.
        del actual_headers['Date']
        self.assertEqual(expected_headers, actual_headers)
        self.assertEqual('Email text', email.content)

    def test_send_html_email_with_attachment(self):
        original_email_count = EmailMessage.objects.count()
        m = mail.EmailMultiAlternatives(
            'Email subject', 'Email text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )

        m.attach_alternative(
            '<html><body><p style="background-color: #AABBFF; color: white">Email html</p></body></html>', 'text/html',
        )

        current_dir = Path(__file__).resolve().parent
        m.attach_file(current_dir / 'test_files' / 'icon.gif', 'image/gif')

        with mail.get_connection('django_mail_viewer.backends.database.backend.EmailBackend') as connection:
            self.assertEqual(1, connection.send_messages([m]))

        # The main message, the multipart/alternative, the text/plain, the text/html, and the attached img/gif
        self.assertEqual(original_email_count + 5, EmailMessage.objects.count())
        email = EmailMessage.objects.filter(parent=None).exclude(message_id='').latest('id')

        parts_test_matrix = {
            'multipart/mixed': {
                'headers': {
                    "Content-Type": "multipart/mixed",
                    "MIME-Version": "1.0",
                    "Subject": "Email subject",
                    "From": "test@example.com",
                    "To": "to1@example.com, to2.example.com",
                    "Message-ID": email.message_id,
                },
                'content': '',
                'attachment': '',
                'parent': None,
            },
            'multipart/alternative': {
                'headers': {'Content-Type': 'multipart/alternative', 'MIME-Version': '1.0',},
                'content': '',
                'attachment': '',
                'parent': email,
            },
            'text/plain': {
                'headers': {
                    'Content-Type': 'text/plain; charset=\"utf-8\"',
                    'MIME-Version': '1.0',
                    'Content-Transfer-Encoding': '7bit',
                },
                'content': 'Email text',
                'attachment': '',
                'parent': email,
            },
            'text/html': {
                'headers': {
                    'Content-Type': 'text/html; charset="utf-8"',
                    'MIME-Version': '1.0',
                    'Content-Transfer-Encoding': '7bit',
                },
                'content': '<html><body><p style="background-color: #AABBFF; color: white">Email html</p></body></html>',
                'attachment': '',
                'parent': email,
            },
            'image/gif': {
                'headers': {
                    'Content-Type': 'image/gif',
                    'MIME-Version': '1.0',
                    'Content-Transfer-Encoding': 'base64',
                    'Content-Disposition': 'attachment; filename="icon.gif"',
                },
                'content': '',
                'attachment': 'mailviewer_attachments/icon.gif',
                'parent': email,
            },
        }

        # This list lets the parts tested be tracked so that the test can validate none of the expected parts were missing
        # due to not being created in the database.
        tested_parts = []
        for part in list(email.parts.all()) + [email]:
            content_type = part.get_content_type()
            self.assertTrue(content_type in parts_test_matrix.keys())
            with self.subTest(content_type=content_type):
                current_test = parts_test_matrix[content_type]
                tested_parts.append(content_type)
                actual_headers = json.loads(part.message_headers)
                if actual_headers.get('Date'):
                    # Now remove the `Date` key so that the dicts can be compared for the multipart/mixed
                    # would love to find a way to properly compare them
                    del actual_headers['Date']
                self.assertEqual(current_test['headers'], actual_headers)
                self.assertEqual(current_test['content'], part.content)
                self.assertEqual(current_test['attachment'], str(part.file_attachment))

        self.assertEqual(list(parts_test_matrix.keys()).sort(), tested_parts.sort())
