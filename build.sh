#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create necessary directories
mkdir -p /opt/render/project/src/tax_form/pdf_templates
mkdir -p /tmp/temp_pdfs
mkdir -p /tmp/media