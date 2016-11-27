=============================
Django Mail Viewer
=============================

.. image:: https://badge.fury.io/py/django-mail-viewer.png
    :target: https://badge.fury.io/py/django-mail-viewer

.. image:: https://travis-ci.org/jmichalicek/django-mail-viewer.png?branch=master
    :target: https://travis-ci.org/jmichalicek/django-mail-viewer

View emails in development without actually sending them.

Documentation
-------------

The full documentation is at https://django-mail-viewer.readthedocs.io.

Quickstart
----------

Install Django Mail Viewer::

    pip install django-mail-viewer

Add it to your `INSTALLED_APPS`:

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

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
