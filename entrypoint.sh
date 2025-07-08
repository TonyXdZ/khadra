#!/bin/bash

# Exit on any error
set -e

echo "Waiting for PostgreSQL to be available..."

# Python-based DB availability check
python << END
import socket
import time

host = "db"          # container service name for PostgreSQL (in docker-compose.yml)
port = 5432          # default PostgreSQL port

while True:
    try:
        socket.create_connection((host, port), timeout=1).close()
        break
    except OSError:
        time.sleep(1)
END

echo "✅ PostgreSQL is available. Continuing..."

# Run migrations and collect static files
echo "Running migrations..."
python manage.py migrate

echo "Starting the server..."
exec "$@"
