from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from ..models import Association, Financial, Extension
from ..forms import ExtensionForm
from datetime import datetime
import os
from .pdf_extension_generation import generate_extension_response
import logging

logger = logging.getLogger(__name__)

class ExtensionFormView(View):
    template_name = 'tax_form/extension_form.html'

    def get(self, request):
        # Handle AJAX request for tax years
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            association_id = request.GET.get('association_id')
            if association_id:
                tax_years = Financial.objects.filter(
                    association_id=association_id
                ).values_list('tax_year', flat=True).distinct().order_by('-tax_year')
                return JsonResponse(list(tax_years), safe=False)
            return JsonResponse([], safe=False)

        context = {
            'form': ExtensionForm(),
            'associations': Association.objects.all().order_by('association_name')
        }

        # Handle regular GET with association_id and tax_year
        association_id = request.GET.get('association_id')
        tax_year = request.GET.get('tax_year')

        if association_id and tax_year:
            try:
                association = Association.objects.get(id=association_id)
                financial = Financial.objects.get(
                    association=association,
                    tax_year=tax_year
                )
                extension, created = Extension.objects.get_or_create(
                    financial=financial,
                    defaults={'filed': False}
                )
                form = ExtensionForm(instance=extension)
                
                context.update({
                    'form': form,
                    'association': association,
                    'tax_year': tax_year,
                    'financial': financial,
                    'extension': extension,
                })
            except (Association.DoesNotExist, Financial.DoesNotExist) as e:
                messages.error(request, "No financial record found for the selected association and year.")
                logger.error(f"Error retrieving records: {str(e)}")

        return render(request, self.template_name, context)

    def post(self, request):
        logger.debug("POST request received")
        logger.debug(f"POST data: {request.POST}")

        association_id = request.POST.get('association_id')
        tax_year = request.POST.get('tax_year')

        if not association_id or not tax_year:
            messages.error(request, "Please select an association and tax year.")
            return redirect('extension_form')

        try:
            association = get_object_or_404(Association, id=association_id)
            financial = get_object_or_404(Financial, association=association, tax_year=tax_year)
            extension, created = Extension.objects.get_or_create(
                financial=financial,
                defaults={'filed': False}
            )
            
            form = ExtensionForm(request.POST, request.FILES, instance=extension)
            if form.is_valid():
                extension = form.save()
                
                # Handle PDF generation if requested
                if 'generate_pdf' in request.POST:
                    logger.debug("Generating PDF...")
                    template_path = os.path.join(settings.PDF_TEMPLATE_DIR, 'template_7004.pdf')
                    logger.debug(f"Template path: {template_path}")
                    
                    # Prepare data for PDF generation
                    pdf_data = {
                        'association_name': association.association_name,
                        'ein': association.ein,
                        'address': association.mailing_address,
                        'city': association.city,
                        'state': association.state,
                        'zipcode': association.zipcode,
                        'tax_year': tax_year,
                        'tentative_tax': form.cleaned_data['tentative_tax'],
                        'total_payments': form.cleaned_data['total_payments'],
                    }

                    # Generate and return PDF response
                    response = generate_extension_response(pdf_data, template_path)
                    if response:
                        return response
                    else:
                        messages.error(request, "Error generating PDF. Please try again.")
                
                messages.success(request, "Extension information saved successfully.")
                return redirect(f'/extension-form/?association_id={association_id}&tax_year={tax_year}')
            
            context = {
                'form': form,
                'association': association,
                'tax_year': tax_year,
                'associations': Association.objects.all().order_by('association_name'),
                'financial': financial,
                'extension': extension,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            logger.error(f"Error processing form: {str(e)}", exc_info=True)
            messages.error(request, f"Error processing form: {str(e)}")
            return redirect('extension_form')