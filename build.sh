#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input --clear

# Run migrations
python manage.py migrate

# Create necessary directories on the persistent disk
mkdir -p /opt/render/project/media/pdf_templates
mkdir -p /opt/render/project/media/temp_pdfs
mkdir -p /opt/render/project/media/extensions
mkdir -p /opt/render/project/media/completed_tax_returns

# Copy PDF templates to persistent disk
cp -r tax_form/pdf_templates/* /opt/render/project/media/pdf_templates/ || echo "No PDF templates to copy or directory doesn't exist"

# Ensure proper permissions
chmod -R 777 /opt/render/project/media