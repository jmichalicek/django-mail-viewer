"""
Test django_mail_viewer.backends
"""
from __future__ import division, absolute_import, unicode_literals

from django.core import mail
from django.test import TestCase

import os


class LocMemBackendTest(TestCase):
    """
    Test django_mail_viewer.backends.locmem.EmailBackend
    """

    def setUp(self):
        mail.outbox = []

    def test_send_messages_adds_message_to_mail_outbox(self):
        """
        send_messages() method should append the sent email.Message to mail.outbox 
        """

        m = mail.EmailMultiAlternatives(
                'Email 2 subject', 'Email 2 text', 'test@example.com',
                ['to1@example.com', 'to2.example.com'])
        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            self.assertEqual([], mail.outbox)
            self.assertEqual(1, connection.send_messages([m]))
            self.assertEqual(1, len(mail.outbox))

    def test_get_message_returns_requested_message(self):

        m = mail.EmailMultiAlternatives(
                'Email 2 subject', 'Email 2 text', 'test@example.com',
                ['to1@example.com', 'to2.example.com'])
        m2 = mail.EmailMultiAlternatives(
                'Email 2 subject', 'Email 2 text', 'test@example.com',
                ['to1@example.com', 'to2.example.com'])

        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            connection.send_messages([m, m2])
            self.assertEqual(2, len(mail.outbox))
            for message in mail.outbox:
                # check that we can use the message id to look up a specific message's data
                self.assertEqual(message, connection.get_message(message.get('Message-ID')))
