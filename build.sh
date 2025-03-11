#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input --clear

# Run migrations
python manage.py migrate

# Create necessary directories on the persistent disk
mkdir -p /media/pdf_templates
mkdir -p /media/temp_pdfs
mkdir -p /media/extensions
mkdir -p /media/completed_tax_returns
mkdir -p /media/signed_engagement_letters

# Copy PDF templates to persistent disk
cp -r tax_form/pdf_templates/* /media/pdf_templates/ || echo "No PDF templates to copy or directory doesn't exist"

# Ensure proper permissions
chmod -R 777 /media
