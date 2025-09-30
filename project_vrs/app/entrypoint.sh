#!/usr/bin/env sh

if [ "$DATABASE" = "postgres" ]; then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
        sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py migrate
# collect static files for WhiteNoise serving (non-fatal if misconfigured)
python manage.py collectstatic --noinput || true
# python manage.py runserver 0.0.0.0:8000
daphne -b 0.0.0.0 -p 8000 backend.asgi:application
