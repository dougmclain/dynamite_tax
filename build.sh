"""
This is a set of changes to fix the media upload permission issues.
"""

# 1. Updated settings.py to ensure MEDIA_ROOT is properly set and exists
# Update the MEDIA_ROOT configuration in HOA_tax/settings.py:

import os
from pathlib import Path

# Media files
MEDIA_URL = '/media/'
if IS_PRODUCTION:
    # Use Render's writable disk mount path
    MEDIA_ROOT = Path('/var/lib/render/disk/media')
    
    # Ensure the directory exists
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    os.makedirs(MEDIA_ROOT / 'completed_tax_returns', exist_ok=True)
    os.makedirs(MEDIA_ROOT / 'extensions', exist_ok=True)
    os.makedirs(MEDIA_ROOT / 'engagement_letters', exist_ok=True)
    os.makedirs(MEDIA_ROOT / 'signed_engagement_letters', exist_ok=True)
else:
    MEDIA_ROOT = Path(BASE_DIR) / 'media'
    os.makedirs(MEDIA_ROOT, exist_ok=True)

# 2. Update the edit_tax_year_info.py view to handle file paths more robustly:

def post(self, request, association_id, tax_year):
    try:
        association = get_object_or_404(Association, id=association_id)
        financial, created = Financial.objects.get_or_create(
            association=association,
            tax_year=tax_year,
            defaults={'total_expenses': 0}
        )
        extension, _ = Extension.objects.get_or_create(financial=financial)
        completed_tax_return, _ = CompletedTaxReturn.objects.get_or_create(financial=financial)

        # Store in session
        request.session['selected_association_id'] = str(association_id)
        request.session['selected_tax_year'] = int(tax_year)

        extension.filed = 'extension_filed' in request.POST
        extension.filed_date = request.POST.get('extension_filed_date') or None
        completed_tax_return.return_filed = 'tax_return_filed' in request.POST
        completed_tax_return.date_prepared = request.POST.get('tax_return_filed_date') or None

        # Handle file uploads
        if 'extension_file' in request.FILES:
            # Create a safe filename
            extension_file = request.FILES['extension_file']
            safe_name = ''.join(c for c in association.association_name if c.isalnum() or c.isspace())
            safe_name = safe_name.replace(' ', '_')
            if len(safe_name) > 30:
                safe_name = safe_name[:30]
                
            # Format the filename
            file_ext = os.path.splitext(extension_file.name)[1].lower()
            new_filename = f"{safe_name}_extension_{tax_year}{file_ext}"
            
            # Delete previous file if it exists
            if extension.form_7004:
                try:
                    if extension.form_7004.storage.exists(extension.form_7004.name):
                        extension.form_7004.delete()
                except Exception as e:
                    logger.warning(f"Could not delete previous extension file: {e}")
                    
            # Save the new file - use save method with name parameter
            extension.form_7004.save(
                f"extensions/{new_filename}", 
                extension_file
            )

        if 'tax_return_file' in request.FILES:
            # Create a safe filename
            tax_return_file = request.FILES['tax_return_file']
            safe_name = ''.join(c for c in association.association_name if c.isalnum() or c.isspace())
            safe_name = safe_name.replace(' ', '_')
            if len(safe_name) > 30:
                safe_name = safe_name[:30]
                
            # Format the filename
            file_ext = os.path.splitext(tax_return_file.name)[1].lower()
            new_filename = f"{safe_name}_tax_return_{tax_year}{file_ext}"
            
            # Delete previous file if it exists
            if completed_tax_return.tax_return_pdf:
                try:
                    if completed_tax_return.tax_return_pdf.storage.exists(completed_tax_return.tax_return_pdf.name):
                        completed_tax_return.tax_return_pdf.delete()
                except Exception as e:
                    logger.warning(f"Could not delete previous tax return file: {e}")
                    
            # Save the new file - use save method with name parameter and explicitly include the subdirectory
            completed_tax_return.tax_return_pdf.save(
                f"completed_tax_returns/{new_filename}", 
                tax_return_file
            )

        extension.save()
        completed_tax_return.save()

        messages.success(request, f'Tax year {tax_year} information updated successfully.')
        return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")
    except Exception as e:
        logger.error(f"Error updating tax year info: {str(e)}", exc_info=True)
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")

# 3. Update build.sh to ensure proper permissions:

#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create necessary directories on the persistent disk with proper permissions
DISK_ROOT="/var/lib/render/disk"
MEDIA_ROOT="${DISK_ROOT}/media"

echo "Setting up directories with proper permissions..."
mkdir -p ${MEDIA_ROOT}
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

# Set permissions - make directories writable
echo "Setting permissions..."
chmod -R 777 ${DISK_ROOT}
find ${DISK_ROOT}/pdf_templates -type f -name "*.pdf" -exec chmod 644 {} \; 2>/dev/null || echo "No PDF files found"

# Show what we've created
echo "Directory structure:"
find ${DISK_ROOT} -type d | sort
echo "Directory permissions:"
ls -la ${DISK_ROOT}
ls -la ${MEDIA_ROOT}

# Collect static files
python manage.py collectstatic --no-input --clear

# Run migrations
python manage.py migrate