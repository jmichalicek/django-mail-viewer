import os

from django.core import mail
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND='django_mail_viewer.backends.locmem.EmailBackend')
class EmailListViewTest(SimpleTestCase):
    URL_NAME = 'mail_viewer_list'

    def test_get_returns_email_list(self):
        mail.outbox = []

        mail.send_mail(
            "Email 1 subject",
            "Email 1 text",
            "test@example.com",
            ['to1@example.com', 'to2.example.com'],
            html_message='<html><body>Email 1 HTML</body></html>',
        )

        # email with attachment
        m = mail.EmailMultiAlternatives(
            'Email 2 subject', 'Email 2 text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        m.attach_alternative(
            '<html><body><p style="background-color: #AABBFF; color: white">Email 2 HTML</p></body></html>', 'text/html'
        )
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
class EmailDetailViewTest(SimpleTestCase):
    URL_NAME = 'mail_viewer_detail'

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        mail.outbox = []

    def _get_detail_url(self, message_id=None):
        if not message_id:
            message_id = mail.outbox[0].get('message-id')
            message_id = message_id.strip('<>')
        return reverse(self.URL_NAME, args=[message_id])

    def test_templates_used(self):
        """
        Test that the full template is used for non-ajax but for htmx/ajax the fragment is returned
        """
        mail.send_mail(
            "Email 1 subject",
            "Email 1 text",
            "test@example.com",
            ['to1@example.com', 'to2.example.com'],
            html_message='<html><body>Email 1 HTML</body></html>',
        )

        test_matrix = [
            # This order is interesting...
            {'headers': {'HTTP_HX_REQUEST': True}, 'template': ['mail_viewer/email_detail_content_fragment.html']},
            {
                'headers': {},
                'template': [
                    'mail_viewer/email_detail.html',
                    'mail_viewer/base.html',
                    'mail_viewer/email_detail_content_fragment.html',
                ],
            },
        ]
        for t in test_matrix:
            with self.subTest(**t['headers']):
                response = self.client.get(self._get_detail_url(), **t['headers'])
                self.assertEqual(200, response.status_code)
                self.assertEqual(t['template'], [template.name for template in response.templates])

    def test_view_context(self):
        mail.send_mail(
            "Email 1 subject",
            "Email 1 text",
            "test@example.com",
            ['to1@example.com', 'to2.example.com'],
            html_message='<html><body>Email 1 HTML</body></html>',
        )

        response = self.client.get(self._get_detail_url())
        self.assertEqual(200, response.status_code)
        expected_context = ['message', 'text_body', 'html_body', 'attachments', 'lookup_id', 'outbox']
        for x in expected_context:
            self.assertTrue(x in response.context)

    def test_get_returns_email_details(self):
        m = mail.EmailMultiAlternatives(
            'Email 2 Subject', 'Email 2 text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        m.attach_alternative(
            '<html><body><p style="background-color: #AABBFF; color: white">Email 2 HTML</p></body></html>', 'text/html'
        )
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
            response.context['html_body'],
        )
        self.assertEqual(
            [{'filename': 'icon.gif', 'content_type': 'image/gif', 'file': None}], response.context['attachments']
        )
        self.assertEqual(mail.outbox[0], response.context['message'])
        self.assertEqual(mail.outbox, response.context['outbox'])
        self.assertEqual(response.context['lookup_id'], message_id.strip('<>'))

    def test_missing_email_redirect_to_list(self):
        """
        If a missing email id is given, rather than 404, this should just redirect back to the list view
        for ease of use.
        """
        response = self.client.get(self._get_detail_url('fake-message-id'))
        self.assertRedirects(response, reverse('mail_viewer_list'))


@override_settings(EMAIL_BACKEND='django_mail_viewer.backends.locmem.EmailBackend')
class EmailAttachmentDownloadViewTest(SimpleTestCase):
    URL_NAME = 'mail_viewer_attachment'

    def setUp(self):
        mail.outbox = []

    def test_get_sends_file_as_attachment(self):
        m = mail.EmailMultiAlternatives(
            'Email 2 Subject', 'Email 2 text', 'test@example.com', ['to1@example.com', 'to2.example.com']
        )
        m.attach_alternative(
            '<html><body><p style="background-color: #AABBFF; color: white">Email 2 HTML</p></body></html>', 'text/html'
        )
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


@override_settings(EMAIL_BACKEND='django_mail_viewer.backends.locmem.EmailBackend')
class EmailDeleteViewTest(SimpleTestCase):
    URL_NAME = 'mail_viewer_delete'

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        mail.outbox = []

    def _get_detail_url(self, message_id=None):
        if not message_id:
            message_id = mail.outbox[0].get('message-id')
            message_id = message_id.strip('<>')
        return reverse(self.URL_NAME, args=[message_id])

    def test_get(self):
        """
        Test GET request to the delete view
        """
        mail.send_mail(
            "Email 1 subject",
            "Email 1 text",
            "test@example.com",
            ['to1@example.com', 'to2.example.com'],
            html_message='<html><body>Email 1 HTML</body></html>',
        )

        with mail.get_connection() as connection:
            self.assertEqual(1, len(list(connection.get_outbox())))

        response = self.client.get(self._get_detail_url())
        self.assertEqual(mail.outbox[0], response.context['message'])

    def test_post(self):
        """
        Test that a POST requests deletes the message
        """
        mail.send_mail(
            "Email 1 subject",
            "Email 1 text",
            "test@example.com",
            ['to1@example.com', 'to2.example.com'],
            html_message='<html><body>Email 1 HTML</body></html>',
        )

        with mail.get_connection() as connection:
            self.assertEqual(1, len(list(connection.get_outbox())))
        response = self.client.post(self._get_detail_url())
        self.assertEqual(302, response.status_code)
        with mail.get_connection() as connection:
            self.assertEqual(0, len(list(connection.get_outbox())))

    def test_post_htmx(self):
        """
        Test an HTMX ajax post
        """
        mail.send_mail(
            "Email 1 subject",
            "Email 1 text",
            "test@example.com",
            ['to1@example.com', 'to2.example.com'],
            html_message='<html><body>Email 1 HTML</body></html>',
        )

        with mail.get_connection() as connection:
            self.assertEqual(1, len(list(connection.get_outbox())))
        response = self.client.post(self._get_detail_url(), HTTP_HX_REQUEST=True)
        self.assertEqual(200, response.status_code)
        with mail.get_connection() as connection:
            self.assertEqual(0, len(list(connection.get_outbox())))
