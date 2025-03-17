# Update tax_form/views/delete_files.py

from django.views import View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.conf import settings
from ..models import Financial
from azure.storage.blob import BlobServiceClient
import logging
import time

logger = logging.getLogger(__name__)

class DeleteFinancialPDFView(LoginRequiredMixin, View):
    """View to handle deletion of financial PDF files."""
    
    def post(self, request, financial_id):
        financial = get_object_or_404(Financial, id=financial_id)
        association_id = financial.association.id
        tax_year = financial.tax_year
        
        # Store in session for redirect
        request.session['selected_association_id'] = str(association_id)
        request.session['selected_tax_year'] = tax_year
        
        if financial.financial_info_pdf:
            file_path = financial.financial_info_pdf.name
            
            try:
                # If using Azure Storage
                if settings.USE_AZURE_STORAGE:
                    # Create Azure connection
                    connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
                    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                    container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER)
                    
                    # Check if blob exists before trying to delete
                    blob_client = container_client.get_blob_client(file_path)
                    blob_exists = True
                    try:
                        blob_client.get_blob_properties()
                    except Exception:
                        blob_exists = False
                    
                    if blob_exists:
                        # Delete the blob
                        blob_client.delete_blob()
                        logger.info(f"Deleted blob: {file_path}")
                        
                        # Add a small delay to ensure Azure storage consistency
                        time.sleep(0.5)
                else:
                    # For local storage
                    import os
                    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        logger.info(f"Deleted local file: {full_path}")
                
                # Clear the file reference in the model
                financial.financial_info_pdf = None
                financial.save()
                
                # Add timestamp to session to force reload of cached content
                request.session['pdf_timestamp'] = int(time.time())
                
                messages.success(request, f"Financial PDF for {financial.association.association_name} - {financial.tax_year} deleted successfully.")
            except Exception as e:
                logger.error(f"Error deleting financial PDF: {str(e)}", exc_info=True)
                messages.error(request, f"Error deleting financial PDF: {str(e)}")
        else:
            messages.warning(request, "No financial PDF file to delete.")
        
        # Redirect back to the association page
        return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")