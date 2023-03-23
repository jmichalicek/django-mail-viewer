"""
Backend for test environment.
"""
from contextlib import contextmanager
from os import getpid
from time import monotonic, sleep

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
        self.cache_keys_lock_key = 'message_keys_lock'

    def send_messages(self, messages):
        msg_count = 0
        for message in messages:
            m = message.message()
            message_id = m.get('message-id')
            self.cache.set(message_id, m)

            # Use a lock key and spinlock
            # to avoid clobbering the value stored in the list of keys
            # if multiple processes are updating this at the same time.
            is_stored = False
            loop_count = 0
            max_loop_count = 100
            while not is_stored:
                loop_count += 1
                if loop_count > max_loop_count:
                    break
                with self.cache_lock(self.cache_keys_lock_key, getpid()) as acquired:
                    if acquired:
                        current_cache_keys = self.cache.get(self.cache_keys_key)
                        if not current_cache_keys:
                            current_cache_keys = []
                        current_cache_keys.append(message_id)
                        self.cache.set(self.cache_keys_key, current_cache_keys)
                        msg_count += 1
                        is_stored = True
                    else:
                        sleep(.01)
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

    DEFAULT_LOCK_EXPIRE = 60 * 3  # Lock expires in 3 minutes

    @contextmanager
    def cache_lock(self, lock_id, oid, lock_expires=DEFAULT_LOCK_EXPIRE):
        """
        Lock an id for the given time using cache backend
        :param lock_id string lock id
        :param oid string thread/process identifier
        :param lock_expires optional number of seconds to lock
        NOTE That we use the lock_expires value without any cushion,
        unlike the original version at
        http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html#cookbook-task-serial
        :return boolean if lock acquired
        """
        timeout_at = monotonic() + lock_expires
        # cache.add fails if the key already exists
        acquired = self.cache.add(lock_id, oid, lock_expires)
        try:
            yield acquired
        finally:
            # we have to use delete to take
            # advantage of using add() for atomic locking
            if acquired and monotonic() < timeout_at:
                # don't release the lock if we exceeded the timeout
                # to lessen the chance of releasing an expired lock
                # owned by someone else.
                self.cache.delete(lock_id)
