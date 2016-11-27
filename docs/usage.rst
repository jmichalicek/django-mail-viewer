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
        url(r'^', include(django_mail_viewer_urls)),
        ...
    ]
