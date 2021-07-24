"""
Django settings for production deployment
"""
from config.settings.common import *

SECRET_KEY = 'django-insecure-5ez*!92$k-nfrpsfoqbhf-cx-u!^5ozei4wd%4i7*6grq3dt-d'

DEBUG = False
ALLOWED_HOSTS = ['localhost', '0.0.0.0', 'campus.readiness.in']
STATIC_ROOT = 'static'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True



