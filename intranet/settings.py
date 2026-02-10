import environ
import os

from pathlib import Path

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='127.0.0.1,localhost').strip().split(',')
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS').strip().split(',')

# Application definition

INSTALLED_APPS = [
    'dal',
    'dal_select2',
    'django.contrib.humanize',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_cotton',
    'crispy_forms',
    'django_tables2',
    'extra_views',
    'django_filters',
    'import_export',
    'django_htmx',
    'widget_tweaks',
    'apps.core',
    'apps.slack',
    'apps.auditoria',
    'apps.rrhh',
    'apps.papeleria',
    'apps.directorio',
    'apps.destajos',
    'apps.fotos',
    'apps.monitoreo_servicios',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.auditoria.middleware.UserAccessLogMiddleware',
    'apps.auditoria.middleware.AuditMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'intranet.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.empresas',
                'apps.core.context_processors.empresa',
            ],
        },
    },
]

WSGI_APPLICATION = 'intranet.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': env.db(),
    'intranet': env.db('INTRANET_DATABASE_URL'),
}

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

COTTON_DIR = 'components'

FOTOS_ROOT = Path(env('FOTOS_ROOT'))

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/"

EMAIL_USE_TLS = True
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('EMAIL_DEFAULT_FROM_EMAIL')

CRISPY_ALLOWED_TEMPLATE_PACKS = "daisyui5"
CRISPY_TEMPLATE_PACK = "daisyui5"

DJANGO_TABLES2_TEMPLATE = "django_tables2/daisyui5.html"

SLACK_BOT_TOKEN = env('SLACK_BOT_TOKEN')
SLACK_TEAM_ID = env('SLACK_TEAM_ID')

CCTV_USER = env('CCTV_USER')
CCTV_PASSWORD = env('CCTV_PASSWORD')

PBX_USER = env('PBX_USER')
PBX_PASSWORD = env('PBX_PASSWORD')

IDRAC_USER = env('IDRAC_USER')
IDRAC_PASSWORD = env('IDRAC_PASSWORD')

CORREO_SOPORTE_TI = env('CORREO_SOPORTE_TI')

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "simple": {
            "format": "[{levelname}] {name}: {message}",
            "style": "{",
        },
        "verbose": {
            "format": "[{asctime}] {levelname} {name} ({funcName}) :: {message}",
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "signals_file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs/signals.log",
            "formatter": "verbose",
        },
    },

    "loggers": {
        "core.network": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "signals": {
            "handlers": ["console", "signals_file"],
            "level": "INFO",
            "propagate": False,
        },
        "auditoria.signals": {
            "handlers": ["console", "signals_file"],
            "level": "INFO",
            "propagate": False,
        },
        "monitoreo_servicios.services.pbx": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "monitoreo_servicios.services.idrac": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
