#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py bootstrap
exec daphne -b 0.0.0.0 -p "${PORT:-8000}" config.asgi:application
