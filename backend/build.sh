#!/usr/bin/env bash
# Build command do Web Service do backend no Render (ver render.yaml).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
