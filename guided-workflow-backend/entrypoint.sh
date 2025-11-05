#!/usr/bin/env bash

# This entrypoint script starts the FastAPI application using Gunicorn with Uvicorn workers.
# The number of workers is set to a WEB_CONCURRENCY, with a default of 5 if WEB_CONCURRENCY is not set.

set -Eeo pipefail

# Set the number of workers to WEB_CONCURRENCY or default to 5
WEB_WORKERS=${WEB_CONCURRENCY:-5}

echo "Starting FastAPI application with $WEB_WORKERS workers..."

set -- "$@" "-w $WEB_WORKERS"
exec "$@"
