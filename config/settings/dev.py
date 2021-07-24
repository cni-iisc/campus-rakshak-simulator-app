"""
Django settings from local/ development deployment
"""
from config.settings.common import *

SECRET_KEY = 'django-insecure-5ez*!92$k-nfrpsfoqbhf-cx-u!^5ozei4wd%4i7*6grq3dt-d'

DEBUG = True
ALLOWED_HOSTS = ['localhost', '0.0.0.0', '10.156.14.2', 'campus.readiness.in']
STATIC_ROOT = 'static'
