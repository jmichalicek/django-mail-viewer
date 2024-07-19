.. :changelog:

History
-------
2.2.0
+++++++
* Added cache lock to prevent errors when using the cache backend with multiple processes by @jimcooley

2.1
+++++++
* Added `allow-same-source-origin` to iframe sandbox so that things like `@font-face` can function on localhost
* Added testing on Django 4.1 and Python 3.11
* Stopped testing on old versions of Python and Django which had already been dropped from setup.py
* Some type hinting fixes

2.0
+++++++
* Dropped Python 3.5 and 2.7 support
* Testing against Django 2.2 to 3.1
* Dropped testing Django versions less than 2.2
* Added new database backend which stores emails in a model in the database

1.0.0 (2018-04-23)
++++++++++++++++++
* Dropped testing of Django 1.8, 1.9 and 1.10
* Stopped using assignment_tag in favor of Django 1.9+ simple_tag functionality, definitely breaking Django 1.8
* Added testing of Django 2.0
* Updated .editorconfig, added flake8 check, isort, and yapf checks and configs

0.2.0 (2017-08-20)
++++++++++++++++++
* Added stats toxenv to show coverage stats
* Corrected v0.1.0 release date in history
* Added setting the Django `EMAIL_BACKEND` setting to quickstart and usage
* Added django cache backend
* Fixed handling of quoted-printable email encoding
* Dropped testing of Django 1.8, added testing of Django 1.11 and Python 3.6

0.1.0 (2016-12-23)
++++++++++++++++++

* First release on PyPI.
