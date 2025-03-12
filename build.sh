#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Set up directories with explicit error handling
DISK_ROOT="/var/lib/render/disk"
MEDIA_ROOT="${DISK_ROOT}/media"

echo "Setting up directories..."
mkdir -p ${MEDIA_ROOT}

# Create media subdirectories with proper permissions
echo "Creating media subdirectories..."
mkdir -p ${MEDIA_ROOT}/engagement_letters
mkdir -p ${MEDIA_ROOT}/signed_engagement_letters
mkdir -p ${MEDIA_ROOT}/extensions
mkdir -p ${MEDIA_ROOT}/completed_tax_returns
mkdir -p ${DISK_ROOT}/pdf_templates
mkdir -p ${DISK_ROOT}/temp_pdfs

# Copy PDF templates from repository to persistent disk
echo "Copying PDF templates from repository..."
if [ -d "pdf_templates" ]; then
    echo "Source templates found at pdf_templates/: $(ls -la pdf_templates/)"
    cp -rv pdf_templates/* ${DISK_ROOT}/pdf_templates/
elif [ -d "tax_form/pdf_templates" ]; then
    echo "Source templates found at tax_form/pdf_templates/: $(ls -la tax_form/pdf_templates/)"
    cp -rv tax_form/pdf_templates/* ${DISK_ROOT}/pdf_templates/
else
    echo "PDF templates directory not found in expected locations"
    echo "Root directory contents:"
    ls -la
fi

# Set permissions - make directories fully writable
echo "Setting permissions..."
chmod -R 777 ${DISK_ROOT}
echo "Disk root permissions set to 777"

# This is critical: we need to set permissions on the parent directory too
if [ -d "/var/lib/render" ]; then
    echo "Setting permissions on /var/lib/render..."
    chmod 777 /var/lib/render
    echo "/var/lib/render permissions: $(ls -la /var/lib/render)"
fi

find ${DISK_ROOT}/pdf_templates -type f -name "*.pdf" -exec chmod 644 {} \; 2>/dev/null || echo "No PDF files found"

# Show what we've created
echo "Directory structure:"
find ${DISK_ROOT} -type d | sort
echo "Directory permissions:"
ls -la ${DISK_ROOT}
ls -la ${MEDIA_ROOT}
ls -la ${MEDIA_ROOT}/completed_tax_returns
ls -la ${MEDIA_ROOT}/extensions

# Collect static files
python manage.py collectstatic --no-input --clear

# Run migrations
python manage.py migrate