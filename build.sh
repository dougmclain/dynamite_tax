#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create necessary directories on the persistent disk
mkdir -p /media/pdf_templates
mkdir -p /media/temp_pdfs
mkdir -p /media/extensions
mkdir -p /media/completed_tax_returns
mkdir -p /media/signed_engagement_letters

# Copy PDF templates - adjust source path if needed
if [ -d "tax_form/pdf_templates" ]; then
    echo "Copying PDF templates from tax_form/pdf_templates"
    cp -r tax_form/pdf_templates/* /media/pdf_templates/
elif [ -d "staticfiles/pdf_templates" ]; then
    echo "Copying PDF templates from staticfiles/pdf_templates"
    cp -r staticfiles/pdf_templates/* /media/pdf_templates/
else
    echo "WARNING: Could not find PDF templates directory"
    # List directories to help diagnose
    echo "Contents of current directory:"
    ls -la
    echo "Contents of tax_form directory (if exists):"
    ls -la tax_form || echo "tax_form directory not found"
fi

# Ensure proper permissions
chmod -R 755 /media

# Collect static files
python manage.py collectstatic --no-input --clear

# Run migrations
python manage.py migrate

# List the contents of /media/pdf_templates for verification
echo "Contents of /media/pdf_templates:"
ls -la /media/pdf_templates || echo "Directory is empty or doesn't exist"