from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from azure.storage.blob import BlobServiceClient
from ..models import Association, Financial, Extension, CompletedTaxReturn
import logging
import os

logger = logging.getLogger(__name__)

# Update the EditTaxYearInfoView in tax_form/views/edit_tax_year_info.py

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
            'financial': financial,  # Add financial to the context
        }
        return render(request, self.template_name, context)

# In tax_form/views/edit_tax_year_info.py
# Update the post method to handle the new fields:

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
            
            # Update tax return sent fields
            completed_tax_return.sent_for_signature = 'tax_return_sent' in request.POST
            completed_tax_return.sent_date = request.POST.get('tax_return_sent_date') or None
            
            # Update filed tax return fields
            completed_tax_return.return_filed = 'tax_return_filed' in request.POST
            completed_tax_return.date_prepared = request.POST.get('tax_return_filed_date') or None
            completed_tax_return.filing_status = request.POST.get('filing_status', 'not_filed')

            # Azure Storage connection
            connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER)

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
                
                # Full path for the blob
                blob_path = f"extensions/{filename}"
                
                # Read file content
                file_content = extension_file.read()
                
                # Upload directly to Azure
                blob_client = container_client.get_blob_client(blob_path)
                blob_client.upload_blob(file_content, overwrite=True, content_type="application/pdf")
                
                # Store the blob path in the model
                extension.form_7004 = blob_path
                logger.info(f"Uploaded extension file to Azure: {blob_path}")

            # Handle sent tax return file upload
            if 'sent_tax_return_file' in request.FILES:
                sent_tax_return_file = request.FILES['sent_tax_return_file']
                logger.debug(f"Received sent tax return file with size: {sent_tax_return_file.size} bytes")

                # Create a safe filename
                safe_name = ''.join(c for c in association.association_name if c.isalnum() or c.isspace())
                safe_name = safe_name.replace(' ', '_')
                if len(safe_name) > 30:
                    safe_name = safe_name[:30]
                
                file_ext = os.path.splitext(sent_tax_return_file.name)[1].lower()
                filename = f"{safe_name}_sent_tax_return_{tax_year}{file_ext}"
                
                # Full path for the blob
                blob_path = f"sent_tax_returns/{filename}"
                
                # Read file content
                file_content = sent_tax_return_file.read()
                
                # Upload directly to Azure
                blob_client = container_client.get_blob_client(blob_path)
                blob_client.upload_blob(file_content, overwrite=True, content_type="application/pdf")
                
                # Store the blob path in the model
                completed_tax_return.sent_tax_return_pdf = blob_path
                logger.info(f"Uploaded sent tax return file to Azure: {blob_path}")

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
                
                # Full path for the blob
                blob_path = f"completed_tax_returns/{filename}"
                
                # Read file content
                file_content = tax_return_file.read()
                
                # Upload directly to Azure
                blob_client = container_client.get_blob_client(blob_path)
                blob_client.upload_blob(file_content, overwrite=True, content_type="application/pdf")
                
                # Store the blob path in the model
                completed_tax_return.tax_return_pdf = blob_path
                logger.info(f"Uploaded tax return file to Azure: {blob_path}")

            # Handle financial info file upload
            if 'financial_info_file' in request.FILES:
                financial_info_file = request.FILES['financial_info_file']
                logger.debug(f"Received financial info file with size: {financial_info_file.size} bytes")

                # Create a safe filename
                safe_name = ''.join(c for c in association.association_name if c.isalnum() or c.isspace())
                safe_name = safe_name.replace(' ', '_')
                if len(safe_name) > 30:
                    safe_name = safe_name[:30]
                
                file_ext = os.path.splitext(financial_info_file.name)[1].lower()
                filename = f"{safe_name}_financial_info_{tax_year}{file_ext}"
                
                # Full path for the blob
                blob_path = f"financial_info/{filename}"
                
                # Read file content
                file_content = financial_info_file.read()
                
                # Upload directly to Azure
                blob_client = container_client.get_blob_client(blob_path)
                blob_client.upload_blob(file_content, overwrite=True, content_type="application/pdf")
                
                # Store the blob path in the model
                financial.financial_info_pdf = blob_path
                logger.info(f"Uploaded financial info file to Azure: {blob_path}")
                financial.save()  # Save financial model changes

            # Save updated models
            extension.save()
            completed_tax_return.save()

            messages.success(request, f'Tax year {tax_year} information updated successfully.')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")
        except Exception as e:
            logger.error(f"Error updating tax year info: {str(e)}", exc_info=True)
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")