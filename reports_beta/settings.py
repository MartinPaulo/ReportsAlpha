"""
Django settings for reports_beta project.

Generated by 'django-admin startproject' using Django 1.9.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import logging

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# https://github.com/dobarkod/django-source-revision/issues/1
SOURCE_REVISION_COMMANDS = [
    'git --git-dir=%s/.git rev-parse --short HEAD' % BASE_DIR,  # for git
]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'g8hkvxw54%k-$ymtp90ig*4ai8c%6ra4p@(&m##6b_#g=@0v)!'

# SECURITY WARNING: don't run with debug turned on in production!
# So default to False...
DEBUG = False
# Unless ALLOWED_HOSTS is overridden the default DEBUG setting will stop
# the server running at startup.
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'reports.apps.ReportsConfig',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'registration',
    'contact'
    # 'reports',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'reports_beta.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'sourcerevision.context_processors.source_revision',
            ],
        },
    },
]

# Following two are settings for
# django-inspectional-registration
REGISTRATION_SUPPLEMENT_CLASS = None
ACCOUNT_ACTIVATION_DAYS = 7  # One week activation window

WSGI_APPLICATION = 'reports_beta.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db', 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Australia/Victoria'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

LOGIN_REDIRECT_URL = '/'

# See:
# http://www.webforefront.com/django/setupdjangologging.html
# https://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/
# https://docs.djangoproject.com/en/1.10/topics/logging/

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'production_logfile': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'logging.FileHandler',
            'filename': '/var/log/flow_reports/production.log',
            'formatter': 'simple'
        },
        'development_logfile': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': '/var/log/flow_reports/dev.log',
            'formatter': 'verbose'
        },
    },
    # By default root is set at WARNING: hence my reports loggers won't
    # show anything at a lower level :(
    # This simply resets it to
    'root': {
        'level': 'DEBUG'
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'development_logfile',
                         'production_logfile'],
        },
        'py.warnings': {
            'handlers': ['console', 'development_logfile'],
        },
        'reports': {
            'handlers': ['console', 'development_logfile'],
        },
    }
}

# From:
# http://stackoverflow.com/questions/1626326/how-to-manage-local-vs-production-settings-in-django
try:
    from reports_beta.local_settings import *
except ImportError as e:
    logging.warning('Local machine settings file not found...')
    pass

# need to be after local settings in order to allow them to override the
# debug flag
if DEBUG:
    logging.warning('Overwriting logging output files...')
    LOGGING.get('handlers').get('production_logfile')[
        'filename'] = '/tmp/flow_reports_production.log'
    LOGGING.get('handlers').get('development_logfile')[
        'filename'] = '/tmp/flow_reports_dev.log'
