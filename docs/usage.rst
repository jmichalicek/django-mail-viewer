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

    # You may want to only include this in development environments

    # Django 2
    urlpatterns = [
        ...
        path('', include('django_mail_viewer.urls')),
        ...
    ]

    # Django 1.11
    urlpatterns = [
        ...
        url(r'^', include('django_mail_viewer.urls')),
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

**django_mail_viewer.backends.database.backend.EmailBackend**:
    The cache backend makes use of Django's ORM to store email messages in the database. By default file attachments
    are stored in your default media storage. You may want to implement your own model by subclassing `AbstractBaseEmailMessage`
    to customize where file attachments are stored such as to put them in a separate private s3 bucket.

    The database backend is in its own Django app so that the models and migrations can be ignored
    if you do not intend to use this backend. To use it add mailviewer_database_backend to your `INSTALLED_APPS`:

    .. code-block:: python

        INSTALLED_APPS = (
            ...
            'django_mail_viewer',
            'django_mail_viewer.backends.database.apps.DatabaseBackendConfig',
            ...
        )

    Set your `EMAIL_BACKEND` in settings.py:

    .. code-block:: python

        EMAIL_BACKEND = 'django_mail_viewer.backends.database.EmailBackend'

    If you are using your own model to store email then this model should also be specfied in the settings

    .. code-block:: pythong

      MAILVIEWER_DATABASE_BACKEND_MODEL = 'my_app.MyModel'
