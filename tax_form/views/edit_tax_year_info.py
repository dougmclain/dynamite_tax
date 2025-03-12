from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from ..models import Association, Financial, Extension, CompletedTaxReturn
import logging
import os

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
                
                # Save directly to storage
                saved_path = default_storage.save(full_path, ContentFile(file_content))
                logger.info(f"Saved extension file directly to storage at: {saved_path}")
                
                # Update the model field with the saved path
                extension.form_7004 = saved_path
                
                # Verify file exists
                exists = default_storage.exists(saved_path)
                url = default_storage.url(saved_path)
                logger.debug(f"Extension file exists check: {exists}, URL: {url}")

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
                
                # Save directly to storage
                saved_path = default_storage.save(full_path, ContentFile(file_content))
                logger.info(f"Saved tax return file directly to storage at: {saved_path}")
                
                # Update the model field with the saved path
                completed_tax_return.tax_return_pdf = saved_path
                
                # Verify file exists
                exists = default_storage.exists(saved_path)
                url = default_storage.url(saved_path)
                logger.debug(f"Tax return file exists check: {exists}, URL: {url}")

            # Save updated models
            extension.save()
            completed_tax_return.save()

            messages.success(request, f'Tax year {tax_year} information updated successfully.')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")
        except Exception as e:
            logger.error(f"Error updating tax year info: {str(e)}", exc_info=True)
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")