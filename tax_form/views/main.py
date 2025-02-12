import logging
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from pathlib import Path
from ..models import Financial, Association, Preparer
from ..forms import TaxFormSelectionForm
from .helpers import calculate_financial_info
from .pdf_generation import generate_pdf

logger = logging.getLogger(__name__)

def index(request):
    """View for the home page."""
    return render(request, 'tax_form/index.html')

@login_required
def form_1120h(request):
    """Handle Form 1120-H generation and display."""
    logger.debug("form_1120h view called")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        logger.debug("AJAX request received")
        association_id = request.GET.get('association_id')
        logger.debug(f"Association ID: {association_id}")

        if association_id:
            tax_years = Financial.objects.filter(
                association_id=association_id
            ).values_list('tax_year', flat=True).distinct().order_by('-tax_year')
            logger.debug(f"Tax years for association {association_id}: {list(tax_years)}")
            return JsonResponse(list(tax_years), safe=False)
        else:
            logger.warning("AJAX request received without association_id")
            return JsonResponse([], safe=False)

    context = {
        'form': TaxFormSelectionForm(),
        'financial_info': {},
        'association': None,
        'preparer': None,
        'financial': None,
    }

    if request.method == 'POST':
        logger.debug("POST request received")
        form = TaxFormSelectionForm(request.POST)
        if form.is_valid():
            logger.debug("Form is valid")
            association = form.cleaned_data['association']
            tax_year = form.cleaned_data['tax_year']
            preparer = form.cleaned_data['preparer']
            logger.debug(f"Association: {association}, Tax Year: {tax_year}, Preparer: {preparer}")

            try:
                financial = get_object_or_404(Financial, association=association, tax_year=tax_year)
                logger.debug(f"Financial record found: {financial}")
                financial_info = calculate_financial_info(financial, association)
                financial_info['tax_year'] = tax_year

                context.update({
                    'form': form,
                    'financial_info': financial_info,
                    'association': association,
                    'preparer': preparer,
                    'financial': financial,
                })

                if 'download_pdf' in request.POST:
                    try:
                        pdf_response = generate_pdf(financial_info, association, preparer, tax_year)
                        return pdf_response
                    except Exception as e:
                        logger.exception("Error generating PDF")
                        messages.error(request, f"Error generating PDF: {str(e)}")
            except Financial.DoesNotExist:
                logger.error(f"No financial record found for association {association} and year {tax_year}")
                messages.error(request, "No financial record found for the selected association and year.")
        else:
            logger.warning("Invalid form submission")
            messages.error(request, "Invalid form submission. Please check your inputs.")

    logger.debug("Rendering form_1120h.html template")
    return render(request, 'tax_form/form_1120h.html', context)