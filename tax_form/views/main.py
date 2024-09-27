from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from ..models import Financial, Association, Preparer
from ..forms import TaxFormSelectionForm
from .helpers import calculate_financial_info
from .pdf_generation import generate_pdf

def index(request):
    """View for the home page."""
    return render(request, 'tax_form/index.html')

def form_1120h(request):
    """View for handling Form 1120-H calculations and display."""
    context = {
        'form': TaxFormSelectionForm(),
        'financial_info': {},
        'association': None,
        'preparer': None,
        'financial': None,
    }

    if request.method == 'POST':
        form = TaxFormSelectionForm(request.POST)
        if form.is_valid():
            association = form.cleaned_data['association']
            tax_year = form.cleaned_data['tax_year']
            preparer = form.cleaned_data['preparer']
            financial = get_object_or_404(Financial, association=association, tax_year=tax_year)

            financial_info = calculate_financial_info(financial, association)
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
                    messages.error(request, f"Error generating PDF: {str(e)}")
        else:
            messages.error(request, "Invalid form submission. Please check your inputs.")

    return render(request, 'tax_form/form_1120h.html', context)