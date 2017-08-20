=====
Usage
=====

To use Django Mail Viewer in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_mail_viewer',
        ...
    )

Add Django Mail Viewer's URL patterns:

.. code-block:: python

    from django_mail_viewer import urls as django_mail_viewer_urls


    urlpatterns = [
        ...
        url(r'^mailviewer/', include(django_mail_viewer_urls)),
        ...
    ]

Set your `EMAIL_BACKEND` in settings.py:

.. code-block:: python

    EMAIL_BACKEND = 'django_mail_viewer.backends.locmem.EmailBackend'


Email Backends
---------------

Configurable email backends are supported to allow storing the emails in different storage back ends for display.
There are currentl two supported email backends with more planned.

**django_mail_viewer.backends.locmem.EmailBackend**:
    The locmem backend works very similarly to Django's built in locmem backend, storing the email in a list
    in the local memory of the process.  If the process running the server, such as *manage.py runserver* is
    restarted for any reason then the stored emails are lost.  If you are using a multi-process or asynchronous
    setup such as sending emails asynchrously from a celery task or using django-channels then these emails
    will likely not be in the local memory for your process serving the view.  If you are sending email directly in
    an http request/response, using celery always eager, etc. then this may work fine for you.

**django_mail_viewer.backends.cache.EmailBackend**:
    The cache backend makes use of Django's cache.  By default it will use the default cache, but you can also specify
    a different cache to use.  If you use locmem cache then you will have the same limitations as with the locmem backend.
    Similarly, using Django's dummy cache will result in no email being stored.  If you use one of Django's built in
    Database, Filesystem, or Memcached backends or a third party backend such as a Redis cache backend then
    you will have access to your email across processes and server restarts.
