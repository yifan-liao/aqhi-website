# -*- coding: utf-8 -*-
'''
Production Configurations

- Use djangosecure
- Use Amazon's S3 for storing static files and uploaded media
- Use mailgun to send emails
- Use Redis on Heroku


'''
from __future__ import absolute_import, unicode_literals

from django.utils import six


from .common import *  # noqa

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured exception if DJANGO_SECRET_KEY not in os.environ
SECRET_KEY = env("DJANGO_SECRET_KEY")

SECURITY_MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
)

# Make sure django.middleware.security.SecurityMiddleware is listed first
MIDDLEWARE_CLASSES = SECURITY_MIDDLEWARE + MIDDLEWARE_CLASSES

# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.9/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['example.com'])
# END SITE CONFIGURATION

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See:
# https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader', 'django.template.loaders.app_directories.Loader', ]),
]

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
DATABASES['default'] = env.db("DATABASE_URL")

# Custom Admin URL, use {% url 'admin:index' %}
# ADMIN_URL = env('DJANGO_ADMIN_URL')

# Your production stuff: Below this line define 3rd party library settings
CORS_ORIGIN_WHITELIST = (
    '127.0.0.1',
)
