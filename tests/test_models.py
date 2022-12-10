from pathlib import Path
import shutil

from django.conf import settings
from django.core import mail
from django.test import TestCase

from django_mail_viewer.backends.database.models import EmailMessage


class DatabaseBackendEmailMessageTest(TestCase):
    connection_backend = 'django_mail_viewer.backends.database.backend.EmailBackend'

    @classmethod
    def setUpTestData(cls):

        m = mail.EmailMultiAlternatives(
            'Email subject', 'Email text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )

        m.attach_alternative(
            '<html><body><p style="background-color: #AABBFF; color: white">Email html</p></body></html>',
            'text/html',
        )

        current_dir = Path(__file__).resolve().parent
        m.attach_file(current_dir / 'test_files' / 'icon.gif', 'image/gif')

        with mail.get_connection(cls.connection_backend) as connection:
            connection.send_messages([m])
        cls.multipart_message = EmailMessage.objects.filter(parent=None).first()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            shutil.rmtree(settings.MEDIA_ROOT)
        finally:
            super().tearDownClass()

    def test_get(self):
        test_matrix = [
            {'header_name': 'Content-Type', 'value': 'multipart/mixed'},
            {'header_name': 'Subject', 'value': 'Email subject'},
        ]
        for t in test_matrix:
            with self.subTest(header=t['header_name']):
                self.assertEqual(self.multipart_message.get(t['header_name']), t['value'])
                # test that looking up by headeris not case sensitive
                self.assertEqual(
                    self.multipart_message.get(t['header_name']), self.multipart_message.get(t['header_name'].lower())
                )

    def test_is_multipart(self):
        self.assertTrue(self.multipart_message.is_multipart())

        with mail.get_connection(self.connection_backend) as connection:
            mail.EmailMultiAlternatives(
                'Not multipart',
                'Not multipart',
                'test@example.com',
                ['to1@example.com', 'to2.example.com'],
                connection=connection,
            ).send()

        m = EmailMessage.objects.filter(parent=None).latest('id')
        self.assertFalse(m.is_multipart())

    def test_walk(self):
        self.assertEqual(
            list(EmailMessage.objects.filter(parent=self.multipart_message).order_by('-created_at', 'id')),
            list(self.multipart_message.walk()),
        )

    def test_get_content_type(self):
        # The main message followed by each of its parts
        expected_content_types = ['multipart/mixed', 'multipart/alternative', 'text/plain', 'text/html', 'image/gif']
        self.assertEqual(
            expected_content_types,
            [m.get_content_type() for m in EmailMessage.objects.all().order_by('created_at', 'id')],
        )

    def test_get_payload(self):
        m = self.multipart_message.parts.exclude(file_attachment='').get()
        # May need to seek back to 0 after this
        self.assertEqual(m.file_attachment.read(), m.get_payload())

    def test_get_filename(self):
        m = self.multipart_message.parts.exclude(file_attachment='').get()
        self.assertEqual('icon.gif', m.get_filename())
