"""
Common Django settings for campussim project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
INSTALLED_APPS = [
    ### Django apps for core functionalitites and packages for static file renders
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    ### Third-party apps that provide additional functionalities
    'rest_framework',
    'anymail',
    'django_celery_results',

    ### Application logic of campussim
    'interface.apps.InterfaceConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' #default primary key field type
AUTH_USER_MODEL = 'interface.userModel' #custom user database table


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = False
USE_L10N = True
USE_TZ = False


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = 'static'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage' #compression for perfomance

# Media files (simulator files that are not directly served to users)
MEDIA_URL = '/media/'
MEDIA_ROOT = Path.joinpath(BASE_DIR, 'media/')

# Celery: handles running asynchronous, background tasks
CELERY_BROKER_URL = 'amqp://localhost'
CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_TASK_MAX_RETRIES = 1

CELERYD_TASK_SOFT_TIME_LIMIT = 240 # 4 minutes
CELERYD_TASK_TIME_LIMIT = 600 # 10 minutes

CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_ROUTES = {
    'interace.tasks.send_mail': 'mailQueue',
    'interface.tasks.run_instantiate': 'instQueue',
    'interface.task.run_simulation': 'simQueue',
}

# Anymail: handles sending out email notifications, when configured
ANYMAIL = {

        }
EMAIL_BACKEND = ''
DEFAULT_FROM_MAIL = ''

# Logging Template
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'interface_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': f'{ BASE_DIR }/log.txt',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s | %(levelname)s | module=%(module)s | %(message)s',
        }
    },
    'loggers':{
        'interface_log': {
            'handlers': ['interface_file'],
            'level': 'DEBUG',
            'propagate': False #handles duplicates
        },
        'celery_log': {
            'handlers': ['interface_file'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}

# Colours for messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}
