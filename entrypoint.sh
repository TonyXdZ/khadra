#!/bin/bash

# Exit on any error
set -e

# --- PostrgeSQL Check ---
echo "Waiting for PostgreSQL to be available..."

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
# --- End PostrgeSQL Check ---
# --- Redis Check ---
echo "Waiting for Redis to be available..."

python << END
import socket
import time

host = "redis"       # container service name for Redis (in docker-compose.yml)
port = 6379          # default Redis port

while True:
    try:
        socket.create_connection((host, port), timeout=1).close()
        break
    except OSError:
        time.sleep(1)
END

echo "✅ Redis is available."
# --- End Redis Check ---

# Run migrations
echo "Running migrations..."
python manage.py migrate

echo "Starting the server..."
exec "$@"
