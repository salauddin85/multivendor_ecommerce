#!/bin/sh
# entrypoint.sh

# Run database migrations
python manage.py migrate --noinput

# Optionally collect static files
python manage.py collectstatic --noinput

# Execute the main command passed to the container
exec "$@"
