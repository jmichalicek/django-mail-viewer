import os

from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse


@override_settings(EMAIL_BACKEND='django_mail_viewer.backends.locmem.EmailBackend')
class EmailListViewTest(TestCase):
    URL_NAME = 'mail_viewer_list'

    def test_get_returns_email_list(self):
        mail.outbox = []

        mail.send_mail("Email 1 subject", "Email 1 text", "test@example.com", ['to1@example.com', 'to2.example.com'],
                       html_message='<html><body>Email 1 HTML</body></html>')

        # email with attachment
        m = mail.EmailMultiAlternatives('Email 2 subject', 'Email 2 text', 'test@example.com',
                                        ['to1@example.com', 'to2.example.com'])
        m.attach_alternative(
            '<html><body><p style="background-color: #AABBFF; color: white">Email 2 HTML</p></body></html>',
            'text/html')
        current_dir = os.path.dirname(__file__)
        files_dir = os.path.join(current_dir, 'test_files')
        test_file_attachment = os.path.join(files_dir, 'icon.gif')
        m.attach_file(test_file_attachment)
        m.send()

        response = self.client.get(reverse(self.URL_NAME))
        self.assertEqual(200, response.status_code)
        self.assertEqual(mail.outbox, response.context['outbox'])
        self.assertEqual(2, len(mail.outbox))
        self.assertEqual(response.context['outbox'][0].get('subject'), 'Email 1 subject')
        self.assertEqual(response.context['outbox'][1].get('subject'), 'Email 2 subject')

    def test_get_with_empty_list_has_200_response(self):
        mail.outbox = []
        response = self.client.get(reverse(self.URL_NAME))
        self.assertEqual(200, response.status_code)


@override_settings(EMAIL_BACKEND='django_mail_viewer.backends.locmem.EmailBackend')
class EmailDetailViewTest(TestCase):
    URL_NAME = 'mail_viewer_detail'

    def _get_detail_url(self, message_id=None):
        if not message_id:
            message_id = mail.outbox[0].get('message-id')
            message_id = message_id.strip('<>')
        return reverse(self.URL_NAME, args=[message_id])

    def test_view_context(self):
        mail.outbox = []
        mail.send_mail("Email 1 subject", "Email 1 text", "test@example.com", ['to1@example.com', 'to2.example.com'],
                       html_message='<html><body>Email 1 HTML</body></html>')

        response = self.client.get(self._get_detail_url())
        self.assertEqual(200, response.status_code)
        expected_context = ['message', 'text_body', 'html_body', 'attachments', 'lookup_id', 'outbox']
        for x in expected_context:
            self.assertTrue(x in response.context)

    def test_get_returns_email_details(self):
        mail.outbox = []
        m = mail.EmailMultiAlternatives('Email 2 Subject', 'Email 2 text', 'test@example.com',
                                        ['to1@example.com', 'to2.example.com'])
        m.attach_alternative(
            '<html><body><p style="background-color: #AABBFF; color: white">Email 2 HTML</p></body></html>',
            'text/html')
        current_dir = os.path.dirname(__file__)
        files_dir = os.path.join(current_dir, 'test_files')
        test_file_attachment = os.path.join(files_dir, 'icon.gif')
        m.attach_file(test_file_attachment)
        m.send()

        message_id = mail.outbox[0].get('message-id')
        response = self.client.get(self._get_detail_url(message_id.strip('<>')))
        self.assertEqual(200, response.status_code)

        self.assertEqual('Email 2 text', response.context['text_body'])
        self.assertEqual(
            '<html><body><p style="background-color: #AABBFF; color: white">Email 2 HTML</p></body></html>',
            response.context['html_body'])
        self.assertEqual([{
            'filename': 'icon.gif',
            'content_type': 'image/gif',
            'file': None
        }], response.context['attachments'])
        self.assertEqual(mail.outbox[0], response.context['message'])
        self.assertEqual(mail.outbox, response.context['outbox'])
        self.assertEqual(response.context['lookup_id'], message_id.strip('<>'))

    def test_missing_email_redirect_to_list(self):
        """
        If a missing email id is given, rather than 404, this should just redirect back to the list view
        for ease of use.
        """
        mail.outbox = []
        response = self.client.get(self._get_detail_url('fake-message-id'))
        self.assertRedirects(response, reverse('mail_viewer_list'))


@override_settings(EMAIL_BACKEND='django_mail_viewer.backends.locmem.EmailBackend')
class EmailAttachmentDownloadViewTest(TestCase):
    URL_NAME = 'mail_viewer_attachment'

    def setUp(self):
        mail.outbox = []

    def test_get_sends_file_as_attachment(self):
        m = mail.EmailMultiAlternatives('Email 2 Subject', 'Email 2 text', 'test@example.com',
                                        ['to1@example.com', 'to2.example.com'])
        m.attach_alternative(
            '<html><body><p style="background-color: #AABBFF; color: white">Email 2 HTML</p></body></html>',
            'text/html')
        current_dir = os.path.dirname(__file__)
        files_dir = os.path.join(current_dir, 'test_files')
        test_file_attachment = os.path.join(files_dir, 'icon.gif')
        m.attach_file(test_file_attachment, 'image/gif')
        m.send()

        message_id = mail.outbox[0].get('message-id').strip('<>')
        response = self.client.get(reverse(self.URL_NAME, args=[message_id, 0]))
        self.assertEqual(200, response.status_code)
        self.assertEqual('image/gif', response['Content-Type'])
        self.assertEqual('attachment; filename=icon.gif', response['Content-Disposition'])
