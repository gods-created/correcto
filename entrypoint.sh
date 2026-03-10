#!/bin/sh

set -e

python -m gunicorn main:correcto \
    --bind 0.0.0.0:8001 \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 60 &

wait