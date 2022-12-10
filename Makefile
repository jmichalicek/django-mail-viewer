.PHONY: clean-pyc clean-build docs help
.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

clean: clean-build clean-pyc

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint: ## check style with flake8
	flake8 django_mail_viewer tests

test: ## run tests quickly with the default Python
	python runtests.py tests

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source django_mail_viewer runtests.py tests
	coverage report -m
	coverage html
	open htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/django-mail-viewer.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ django_mail_viewer
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

release: clean ## package and upload a release
	python setup.py sdist bdist_wheel
	# python setup.py sdist upload
	# python setup.py bdist_wheel upload

sdist: clean ## package
	python setup.py sdist
	ls -l dist

wheel: clean
	python setup.py bdist_wheel

pypi-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

pypi:
	twine upload dist/*

setup-and-run:	setup migrate run

venv:
	 python -m venv .venv

run:
	python manage.py runserver 0.0.0.0:8000

migrate:
	python manage.py migrate

dev:
	docker compose run --service-ports django /bin/bash
shell:
	docker compose exec django /bin/bash

install-mailviewer:
	pip install -e /django/mailviewer --no-binary :all:
