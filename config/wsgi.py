"""Entrée WSGI : utilisée par Vercel (fonction serverless) et par gunicorn (repli Docker)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
