from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from azure.storage.blob import BlobServiceClient, ContentSettings
from ..models import Association, Financial, Extension, CompletedTaxReturn
import logging
import os
import time

logger = logging.getLogger(__name__)

class EditTaxYearInfoView(LoginRequiredMixin, View):
    template_name = 'tax_form/edit_tax_year_info.html'

    def get(self, request, association_id, tax_year):
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

        context = {
            'association': association,
            'tax_year': tax_year,
            'extension': extension,
            'completed_tax_return': completed_tax_return,
        }
        return render(request, self.template_name, context)

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

            # Update model fields from form data
            extension.filed = 'extension_filed' in request.POST
            extension.filed_date = request.POST.get('extension_filed_date') or None
            completed_tax_return.return_filed = 'tax_return_filed' in request.POST
            completed_tax_return.date_prepared = request.POST.get('tax_return_filed_date') or None

            # Handle extension file upload
            if 'extension_file' in request.FILES:
                extension_file = request.FILES['extension_file']
                logger.debug(f"Received extension file with size: {extension_file.size} bytes")

                # Create a safe filename
                safe_name = ''.join(c for c in association.association_name if c.isalnum() or c.isspace())
                safe_name = safe_name.replace(' ', '_')
                if len(safe_name) > 30:
                    safe_name = safe_name[:30]
                
                file_ext = os.path.splitext(extension_file.name)[1].lower()
                filename = f"{safe_name}_extension_{tax_year}{file_ext}"
                
                # Full path including the folder
                full_path = f"extensions/{filename}"
                logger.debug(f"Using full path for extension: {full_path}")
                
                # Delete previous file if it exists
                if extension.form_7004:
                    old_path = extension.form_7004.name
                    logger.debug(f"Checking if old extension file exists: {old_path}")
                    try:
                        if default_storage.exists(old_path):
                            logger.debug(f"Deleting old extension file: {old_path}")
                            default_storage.delete(old_path)
                    except Exception as e:
                        logger.warning(f"Could not delete previous extension file: {e}")
                
                # Read the file content
                file_content = extension_file.read()
                
                # Save with explicit blob properties for public access
                try:
                    # Connect to Azure directly for more control
                    connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
                    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                    container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER)
                    
                    # Set content settings for public access
                    content_settings = ContentSettings(
                        content_type='application/pdf',
                        cache_control='public, max-age=86400'
                    )
                    
                    # Upload the blob with public access
                    blob_client = container_client.get_blob_client(full_path)
                    blob_client.upload_blob(file_content, overwrite=True, content_settings=content_settings)
                    
                    logger.info(f"Uploaded extension file directly to Azure at: {full_path}")
                    
                    # Update model with correct path
                    extension.form_7004 = full_path
                    
                    # Get the URL directly from the blob client
                    blob_url = blob_client.url
                    logger.debug(f"Direct extension blob URL: {blob_url}")
                    
                except Exception as azure_error:
                    logger.error(f"Error with direct Azure upload for extension: {str(azure_error)}", exc_info=True)
                    
                    # Fall back to Django's default_storage if direct upload fails
                    logger.info("Falling back to Django's default_storage for extension file")
                    saved_path = default_storage.save(full_path, ContentFile(file_content))
                    logger.info(f"Saved extension file to: {saved_path}")
                    extension.form_7004 = saved_path
                
                # Verify file exists (try multiple times with a delay)
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    exists = default_storage.exists(extension.form_7004.name)
                    logger.debug(f"Extension file exists check (attempt {attempt}/{max_attempts}): {exists}")
                    
                    if exists:
                        # Get the URL once more for logging
                        url = default_storage.url(extension.form_7004.name)
                        logger.debug(f"Final URL for extension file: {url}")
                        break
                        
                    if attempt < max_attempts:
                        time.sleep(1)  # Wait 1 second before retrying

            # Handle tax return file upload
            if 'tax_return_file' in request.FILES:
                tax_return_file = request.FILES['tax_return_file']
                logger.debug(f"Received tax return file with size: {tax_return_file.size} bytes")

                # Create a safe filename
                safe_name = ''.join(c for c in association.association_name if c.isalnum() or c.isspace())
                safe_name = safe_name.replace(' ', '_')
                if len(safe_name) > 30:
                    safe_name = safe_name[:30]
                
                file_ext = os.path.splitext(tax_return_file.name)[1].lower()
                filename = f"{safe_name}_tax_return_{tax_year}{file_ext}"
                
                # Full path including the folder
                full_path = f"completed_tax_returns/{filename}"
                logger.debug(f"Using full path for tax return: {full_path}")
                
                # Delete previous file if it exists
                if completed_tax_return.tax_return_pdf:
                    old_path = completed_tax_return.tax_return_pdf.name
                    logger.debug(f"Checking if old tax return file exists: {old_path}")
                    try:
                        if default_storage.exists(old_path):
                            logger.debug(f"Deleting old tax return file: {old_path}")
                            default_storage.delete(old_path)
                    except Exception as e:
                        logger.warning(f"Could not delete previous tax return file: {e}")
                
                # Read the file content
                file_content = tax_return_file.read()
                
                # Save with explicit blob properties for public access
                try:
                    # Connect to Azure directly for more control
                    connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
                    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                    container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER)
                    
                    # Set content settings for public access
                    content_settings = ContentSettings(
                        content_type='application/pdf',
                        cache_control='public, max-age=86400'
                    )
                    
                    # Upload the blob with public access
                    blob_client = container_client.get_blob_client(full_path)
                    blob_client.upload_blob(file_content, overwrite=True, content_settings=content_settings)
                    
                    logger.info(f"Uploaded tax return file directly to Azure at: {full_path}")
                    
                    # Update model with correct path
                    completed_tax_return.tax_return_pdf = full_path
                    
                    # Get the URL directly from the blob client
                    blob_url = blob_client.url
                    logger.debug(f"Direct tax return blob URL: {blob_url}")
                    
                except Exception as azure_error:
                    logger.error(f"Error with direct Azure upload for tax return: {str(azure_error)}", exc_info=True)
                    
                    # Fall back to Django's default_storage if direct upload fails
                    logger.info("Falling back to Django's default_storage for tax return file")
                    saved_path = default_storage.save(full_path, ContentFile(file_content))
                    logger.info(f"Saved tax return file to: {saved_path}")
                    completed_tax_return.tax_return_pdf = saved_path
                
                # Verify file exists (try multiple times with a delay)
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    exists = default_storage.exists(completed_tax_return.tax_return_pdf.name)
                    logger.debug(f"Tax return file exists check (attempt {attempt}/{max_attempts}): {exists}")
                    
                    if exists:
                        # Get the URL once more for logging
                        url = default_storage.url(completed_tax_return.tax_return_pdf.name)
                        logger.debug(f"Final URL for tax return file: {url}")
                        break
                        
                    if attempt < max_attempts:
                        time.sleep(1)  # Wait 1 second before retrying

            # Save updated models
            extension.save()
            completed_tax_return.save()

            messages.success(request, f'Tax year {tax_year} information updated successfully.')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")
        except Exception as e:
            logger.error(f"Error updating tax year info: {str(e)}", exc_info=True)
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")