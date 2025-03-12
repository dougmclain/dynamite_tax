#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create directories on the persistent disk
echo "Creating necessary directories..."
mkdir -p /data/pdf_templates
mkdir -p /data/temp_pdfs
mkdir -p /data/media
mkdir -p /data/media/extensions
mkdir -p /data/media/completed_tax_returns
mkdir -p /data/media/signed_engagement_letters

# Copy PDF templates from repository to persistent disk
echo "Copying PDF templates from repository..."
if [ -d "pdf_templates" ]; then
    echo "Source templates found at pdf_templates/: $(ls -la pdf_templates/)"
    cp -rv pdf_templates/* /data/pdf_templates/
elif [ -d "tax_form/pdf_templates" ]; then
    echo "Source templates found at tax_form/pdf_templates/: $(ls -la tax_form/pdf_templates/)"
    cp -rv tax_form/pdf_templates/* /data/pdf_templates/
else
    echo "PDF templates directory not found in expected locations"
    echo "Root directory contents:"
    ls -la
fi

# Set permissions
echo "Setting permissions..."
chmod -R 755 /data
find /data/pdf_templates -type f -name "*.pdf" -exec chmod 644 {} \;

# Show what we've created
echo "Directory structure:"
find /data -type d | sort

# Collect static files
python manage.py collectstatic --no-input --clear

# Run migrations
python manage.py migrate