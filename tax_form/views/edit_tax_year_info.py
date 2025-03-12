from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.files.storage import default_storage
from ..models import Association, Financial, Extension, CompletedTaxReturn
from ..pdf_utils import check_file_exists, delete_file_from_azure
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

            extension.filed = 'extension_filed' in request.POST
            extension.filed_date = request.POST.get('extension_filed_date') or None
            completed_tax_return.return_filed = 'tax_return_filed' in request.POST
            completed_tax_return.date_prepared = request.POST.get('tax_return_filed_date') or None

            # Handle file uploads using default_storage (which is Azure in production)
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
                        # Use default_storage to check and delete files
                        if default_storage.exists(extension.form_7004.name):
                            default_storage.delete(extension.form_7004.name)
                            logger.info(f"Deleted previous extension file: {extension.form_7004.name}")
                    except Exception as e:
                        logger.warning(f"Could not delete previous extension file: {e}")
                
                # Save using default_storage (which will be Azure in production)
                extension.form_7004.save(new_filename, extension_file)


                logger.info(f"Saved extension file to: {extension.form_7004.name}")

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
                        # Using default_storage which will be Azure in production
                        if default_storage.exists(completed_tax_return.tax_return_pdf.name):
                            default_storage.delete(completed_tax_return.tax_return_pdf.name)
                            logger.info(f"Deleted previous tax return file: {completed_tax_return.tax_return_pdf.name}")
                    except Exception as e:
                        logger.warning(f"Could not delete previous tax return file: {e}")
                
                # Save using default_storage (which will be Azure in production)
                completed_tax_return.tax_return_pdf.save(new_filename, tax_return_file)


                logger.info(f"Saved tax return file to: {completed_tax_return.tax_return_pdf.name}")

            extension.save()
            completed_tax_return.save()

            messages.success(request, f'Tax year {tax_year} information updated successfully.')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")
        except Exception as e:
            logger.error(f"Error updating tax year info: {str(e)}", exc_info=True)
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")