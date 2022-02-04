# scimv2-bridge

This is a bridge providing SCIM 2.0 REST API, that can be deployed on a SSSD client and queries the user identities from the SSSD id provider.

## Installation

Create and activate a python virtual env

```bash
$ python3 -m venv bridge-env
$ source bridge-env/bin/activate
```

Install the requirements

```bash
$ pip install django==3.0
$ pip install django-scim2
$ pip install django-extensions
$ pip install django-oauth-toolkit
```

Prepare the models and create the local database

```bash
$ cd src/scimv2-bridge
$ python manage.py makemigrations scimv2bridge
$ python manage.py migrate
```

Create the admin user and start the scimv2-bridge server

```bash
$ python manage.py createsuperuser
$ python manage.py runserver
```
