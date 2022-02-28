# scimv2-bridge

This is a bridge providing SCIM 2.0 REST API, that can be deployed on a SSSD client and queries the user identities from the SSSD id provider.

## Installation

### SSSD preparation

Enroll the host as an IPA client:

```bash
$ ipa-client-install --domain ipa.test --realm IPA.TEST --principal admin --password Secret123 -U
```

The previous step creates a [domain/ipa.test] section in /etc/sssd/sssd.conf
but sssd.conf needs to be customized in order to return additional attributes.

The following script modifies sssd.conf:

```bash
$ cd $SCIMV2_BRIDGE/src/install
$ ./prepare_sssd.py
```

### Django preparation

Create and activate a python virtual env

```bash
$ python3 -m venv --system-site-packages bridge-env
$ source bridge-env/bin/activate
```

Install the requirements

```bash
$ pip install django
$ pip install django-scim2
$ pip install django-extensions
$ pip install django-oauth-toolkit
```

Prepare the models and create the local database

```bash
$ cd $SCIMV2_BRIDGE/src/scimv2-bridge
$ python manage.py makemigrations scimv2bridge
$ python manage.py migrate
```

Create the djangoadmin user and start the scimv2-bridge server

Note: do not use "admin" name as it conflicts with IPA "admin" user

```bash
$ python manage.py createsuperuser
$ python manage.py runserver
```
