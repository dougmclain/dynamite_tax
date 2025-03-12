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

# Copy PDF templates from repository to persistent disk
echo "Copying PDF templates from repository to media disk..."
if [ -d "pdf_templates" ]; then
    # List the source templates for debugging
    echo "Source templates found: $(ls -la pdf_templates/)"
    
    # Copy with verbose output
    cp -rv pdf_templates/* /media/pdf_templates/
    
    # List the destination to verify
    echo "Templates copied to destination: $(ls -la /media/pdf_templates/)"
else
    echo "ERROR: PDF templates directory not found in repository"
    # List root directory to see what's available
    echo "Root directory contents:"
    ls -la
fi

# Ensure proper permissions on media directories
chmod -R 755 /media
chmod 644 /media/pdf_templates/*.pdf 2>/dev/null || echo "No PDF files to set permissions on"

# Print disk usage for debugging
echo "Disk usage:"
df -h