"""
Test django_mail_viewer.backends
"""
import json
import shutil
import threading
import time
from pathlib import Path

from django.conf import settings
from django.core import cache, mail
from django.test import SimpleTestCase, TestCase

from django_mail_viewer.backends.database.models import EmailMessage
from typing import Any


def send_plaintext_messages(count: int, connection: Any):
    for x in range(count):
        mail.EmailMultiAlternatives(
            f'Email subject {x}',
            f'Email text {x}',
            'test@example.com',
            ['to1@example.com', 'to2.example.com'],
            connection=connection,
        ).send()


class LocMemBackendTest(SimpleTestCase):
    """
    Test django_mail_viewer.backends.locmem.EmailBackend
    """

    connection_backend = 'django_mail_viewer.backends.locmem.EmailBackend'

    def setUp(self):
        mail.outbox = []

    def test_send_messages_adds_message_to_mail_outbox(self):
        """
        send_messages() method should append the sent email.Message to mail.outbox
        """

        m = mail.EmailMultiAlternatives(
            'Email 2 subject', 'Email 2 text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        with mail.get_connection(self.connection_backend) as connection:
            self.assertEqual([], mail.outbox)
            self.assertEqual(1, connection.send_messages([m]))
            self.assertEqual(1, len(mail.outbox))

    def test_get_message(self):

        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            send_plaintext_messages(2, connection)
            self.assertEqual(2, len(mail.outbox))
            for message in mail.outbox:
                # check that we can use the message id to look up a specific message's data
                self.assertEqual(message, connection.get_message(message.get('Message-ID')))

    def test_get_outbox(self):
        with mail.get_connection(self.connection_backend) as connection:
            send_plaintext_messages(1, connection)
            self.assertEqual(1, len(connection.get_outbox()))
            send_plaintext_messages(1, connection)
            self.assertEqual(2, len(connection.get_outbox()))
            self.assertEqual(mail.outbox, connection.get_outbox())

    def test_delete_message(self):
        """
        Test the delete() method of the backend deletes the message from the outbox
        """
        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            send_plaintext_messages(3, connection)
            target_message = connection.get_outbox()[1]
            target_id = target_message.get('message-id')
            connection.delete_message(target_id)
            self.assertEqual(2, len(connection.get_outbox()))
            for message in connection.get_outbox():
                self.assertNotEqual(
                    target_id, message.get('message-id'), f'Message with id {target_id} found in outbox after delete.'
                )


class CacheBackendTest(SimpleTestCase):
    """
    Test django_mail_viewer.backends.cache.EmailBackend
    """

    maxDiff = None
    connection_backend = 'django_mail_viewer.backends.cache.EmailBackend'

    def setUp(self):
        # not sure this is the best way to do this, but it'll work for now
        self.mail_cache = cache.caches[settings.MAILVIEWER_CACHE]
        self.mail_cache.clear()

    def test_send_messages_adds_message_to_cache(self):
        m = mail.EmailMultiAlternatives(
            'Email 2 subject', 'Email 2 text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        with mail.get_connection(self.connection_backend) as connection:
            self.mail_cache.delete(connection.cache_keys_key)
            self.assertIsNone(self.mail_cache.get(connection.get_outbox()))
            self.assertEqual(1, connection.send_messages([m]))
            self.assertEqual(1, len(self.mail_cache.get(connection.cache_keys_key)))

    def test_get_message(self):
        """
        Test using get_message() to look up a specific message.
        """

        with mail.get_connection(self.connection_backend) as connection:
            send_plaintext_messages(2, connection)
            for message_id in self.mail_cache.get(connection.cache_keys_key):
                # Not so obvious test here - we know our message ids from the cache, so we just check that looking up
                # by the message id gets us an email message with the same Message-ID headers
                # Could also iterate over connection.get_outbox()
                self.assertEqual(message_id, connection.get_message(message_id).get('Message-ID'))

    def test_get_outbox(self):
        with mail.get_connection(self.connection_backend) as connection:
            send_plaintext_messages(1, connection)
            self.assertEqual(1, len(connection.get_outbox()))
            send_plaintext_messages(1, connection)
            self.assertEqual(2, len(connection.get_outbox()))

            # TODO: A better comparison of the objects. This works for now, though
            message_cache_keys = cache.caches[settings.MAILVIEWER_CACHE].get(connection.cache_keys_key)
            expected = [
                m.get('Message-ID')
                for m in cache.caches[settings.MAILVIEWER_CACHE].get_many(message_cache_keys).values()
            ]
            actual = [m.get('Message-ID') for m in connection.get_outbox()]
            self.assertEqual(expected, actual)

    def test_delete_message(self):
        """
        Test the delete() method of the backend deletes the message from the outbox
        """
        with mail.get_connection(self.connection_backend) as connection:
            send_plaintext_messages(3, connection)
            target_message = connection.get_outbox()[1]
            target_id = target_message.get('message-id')
            connection.delete_message(target_id)
            self.assertEqual(2, len(connection.get_outbox()))
            for message in connection.get_outbox():
                self.assertNotEqual(
                    target_id, message.get('message-id'), f'Message with id {target_id} found in outbox after delete.'
                )

    def test_cache_lock(self):
        """
        Test that the cache_lock() method works with multiple threads.
        """
        results = []
        concurrency = 5
        with mail.get_connection(self.connection_backend) as connection:
            def concurrent(results):
                try:
                    myid = "123-%s" % threading.current_thread().ident
                    with connection.cache_lock("test-lock", myid, 10) as acquired:
                        if acquired:
                            results.append(True)
                            time.sleep(1)
                        else:
                            results.append(False)
                except Exception:
                    results.append(False)
            threads = []
            for i in range(concurrency):
                threads.append(threading.Thread(target=concurrent, args=(results,)))
            for t in threads:
                # start processing concurrent(results) in multiple threads
                t.start()
            for t in threads:
                # wait for all threads to finish
                t.join()

        # Only one thread should have acquired the lock
        self.assertEqual(concurrency, len(results))
        self.assertEqual(1, len([val for val in results if val]))

    def test_concurrent_send_messages_with_cache_lock(self):
        """
        Test that multiple messages sent simultaneously are added to the cache.
        """
        messages = []
        for i in range(3, 8):
            m = mail.EmailMultiAlternatives(
                f'Email {i} subject', f'Email {i} text', 'test_multi@example.com', [f'to{i}@example.com']
            )
            messages.append(m)
        with mail.get_connection(self.connection_backend) as connection:
            self.mail_cache.delete(connection.cache_keys_key)
            self.assertIsNone(self.mail_cache.get(connection.get_outbox()))
            threads = []
            for m in messages:
                threads.append(threading.Thread(target=connection.send_messages, args=([m],)))
            for t in threads:
                t.start()
            for t in threads:
                # wait for all threads to finish
                t.join()
            cache_keys = self.mail_cache.get(connection.cache_keys_key)
            self.assertEqual(5, len(cache_keys))
            original_messages_before_message_id = [m.message().as_string().split('Message-ID:')[0] for m in messages]
            for key in cache_keys:
                sent_message_before_message_id = self.mail_cache.get(key).as_string().split('Message-ID:')[0]
                self.assertIn(sent_message_before_message_id, original_messages_before_message_id)


class DatabaseBackendTest(TestCase):
    """
    Test django_mail_viewer.backends.cache.EmailBackend
    """

    connection_backend = 'django_mail_viewer.backends.database.backend.EmailBackend'

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            shutil.rmtree(settings.MEDIA_ROOT)
        finally:
            super().tearDownClass()

    def test_send_plaintext_email(self):
        original_email_count = EmailMessage.objects.count()
        m = mail.EmailMultiAlternatives(
            'Email subject', 'Email text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        with mail.get_connection(self.connection_backend) as connection:
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
            '<html><body><p style="background-color: #AABBFF; color: white">Email html</p></body></html>',
            'text/html',
        )

        current_dir = Path(__file__).resolve().parent
        m.attach_file(current_dir / 'test_files' / 'icon.gif', 'image/gif')

        with mail.get_connection(self.connection_backend) as connection:
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
                'headers': {
                    'Content-Type': 'multipart/alternative',
                    'MIME-Version': '1.0',
                },
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

    def test_get_message(self):
        """
        Test using get_message() to look up a specific message.
        """

        with mail.get_connection(self.connection_backend) as connection:
            send_plaintext_messages(2, connection)
            self.assertEqual(2, EmailMessage.objects.count())
            for m in EmailMessage.objects.filter(parent=None):
                self.assertEqual(m, connection.get_message(m.message_id))

    def test_get_outbox(self):
        with mail.get_connection(self.connection_backend) as connection:
            send_plaintext_messages(1, connection)
            self.assertEqual(1, len(connection.get_outbox()))
            send_plaintext_messages(1, connection)
            self.assertEqual(2, len(connection.get_outbox()))
            self.assertEqual(list(EmailMessage.objects.all()), list(connection.get_outbox()))

    def test_delete_message(self):
        """
        Test the delete() method of the backend deletes the message from the outbox
        """
        with mail.get_connection(self.connection_backend) as connection:
            send_plaintext_messages(3, connection)
            target_message = connection.get_outbox()[1]
            target_id = target_message.get('message-id')
            connection.delete_message(target_id)
            self.assertEqual(2, len(connection.get_outbox()))
            for message in connection.get_outbox():
                self.assertNotEqual(
                    target_id, message.get('message-id'), f'Message with id {target_id} found in outbox after delete.'
                )
