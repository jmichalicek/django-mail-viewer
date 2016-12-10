from __future__ import division, absolute_import, unicode_literals
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings


@override_settings(EMAIL_BACKEND='django_mail_viewer.backends.locmem.EmailBackend')
class EmailListViewTest(TestCase):
    URL_NAME = 'mail_viewer_list'

    def test_get_returns_email_list(self):
        mail.outbox = []
        ### TEMP FAKE STUFF JUST TO SEE IT WORK

        mail.send_mail(
            "Email 1 subject",
            "Email 1 text",
            "test@example.com",
            ['to1@example.com', 'to2.example.com'],
            html_message='<html><body>Email 1 HTML</body></html>')

        # email with attachment
        m = mail.EmailMultiAlternatives(
                'Email 2 Subject', 'Email 2 text', 'test@example.com',
                ['to1@example.com', 'to2.example.com'],
                 connection=connection)
        m.attach_alternative(
                '<html><body><p style="background-color: #AABBFF; color: white">Email 2 HTML</p></body></html>', 'text/html')
        current_dir = os.path.dirname(__file__)
        files_dir = os.path.join(current_dir, 'test_files')
        test_file_attachment = os.path.join(files_dir, 'icon.gif')
        m.attach_file(test_file_attachment)
        m.send()

        response = self.client.get()
        self.assertEqual(200, response.status_code)
        self.assertEqual(mail.outbox, response.context['outbox'])
        self.assertEqual(2, len(mail.outbox))
        self.assertEqual(response.context['outbox'][0].subject = 'EMail 1 subject')
        self.assertEqual(response.context['outbox'][1].subject = 'EMail 2 subject')

    def test_get_with_empty_list_has_200_response(self):
        mail.outbox = []
        self.assertEqual(200, response.status_code)


@override_settings(EMAIL_BACKEND='django_mail_viewer.backends.locmem.EmailBackend')
class EmailDetailViewTest(TestCase):

    def test_get_returns_email_details(self):
        pass


@override_settings(EMAIL_BACKEND='django_mail_viewer.backends.locmem.EmailBackend')
class EmailAttachmentDownloadViewTest(TestCase):

    def test_get_sends_file_as_attachment(self):
        pass
