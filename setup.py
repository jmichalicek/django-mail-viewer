#!/usr/bin/env python
import os
import sys

from setuptools import find_packages, setup

version = '2.2.0'

if sys.argv[-1] == 'publish':
    try:
        import wheel

        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()

setup(
    name='django-mail-viewer',
    version=version,
    description="""View emails in development without actually sending them.""",
    long_description=readme,
    author='Justin Michalicek',
    author_email='jmichalicek@gmail.com',
    url='https://github.com/jmichalicek/django-mail-viewer',
    packages=find_packages(exclude=['tests', 'docs']),
    include_package_data=True,
    install_requires=[],
    license="MIT",
    zip_safe=False,
    keywords=['django-mail-viewer', 'django', 'email',],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
