#!/usr/bin/env bash
# Azure App Service startup script for the Django backend.
# Configure in Azure Portal → Web App → Configuration → General settings → Startup Command:
#   bash startup.sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn solita_salon.wsgi \
    --bind=0.0.0.0:8000 \
    --workers=2 \
    --timeout=120 \
    --access-logfile '-' \
    --error-logfile '-'
