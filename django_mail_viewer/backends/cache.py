"""
Backend for test environment.
"""
from django.core import cache
from django.core.mail.backends.base import BaseEmailBackend

from .. import settings as mailviewer_settings


class EmailBackend(BaseEmailBackend):
    """
    An email backend to use during testing and local development with Django Mail Viewer.

    Uses Django's cache framework to store sent emails in the cache so that they can
    be easily retrieved in multi-process environments such as using Django Channels or
    when sending an email from a python shell.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = cache.caches[mailviewer_settings.MAILVIEWER_CACHE]
        # a cache entry with a list of the rest of the cache keys
        # This is for get_outbox() so that the system knows which cache keys are there
        # to retrieve them. Django does not have a built in way to get the keys
        # which exist in the cache.
        self.cache_keys_key = 'message_keys'

    def send_messages(self, messages):
        msg_count = 0
        for message in messages:
            m = message.message()
            message_id = m.get('message-id')
            self.cache.set(message_id, m)

            # if multiple processes are updating this at the same time then
            # things will get hung up.  May introduce a lock key and spinlock
            # to avoid clobbering the value stored in the list of keys.
            current_cache_keys = self.cache.get(self.cache_keys_key)
            if not current_cache_keys:
                current_cache_keys = []
            current_cache_keys.append(message_id)
            self.cache.set(self.cache_keys_key, current_cache_keys)
            msg_count += 1
        return msg_count

    def get_message(self, lookup_id):
        """
        Look up and return a specific message in the outbox
        """
        return self.cache.get(lookup_id)

    def get_outbox(self, *args, **kwargs):
        """
        Get the outbox used by this backend.  This backend returns a copy of mail.outbox.
        May add pagination args/kwargs.
        """
        # grabs all of the keys in the stored self.cache_keys_key
        # and passes those into get_many() to retrieve the keys
        message_keys = self.cache.get(self.cache_keys_key)
        if message_keys:
            messages = list(self.cache.get_many(message_keys).values())
        else:
            messages = []
        return messages

    def delete_message(self, message_id: str):
        """
        Remove the message with the given id from the mailbox
        """
        message_keys = self.cache.get(self.cache_keys_key, [])
        message_keys.remove(message_id)
        self.cache.set(self.cache_keys_key, message_keys)
        self.cache.delete(message_id)


