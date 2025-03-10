from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Financial, Association
from ..forms import FinancialForm
import logging

logger = logging.getLogger(__name__)

@login_required
def create_financial(request):
    """View for creating or updating financial information."""
    # Try to get values from GET parameters first
    association_id = request.GET.get('association')
    tax_year = request.GET.get('tax_year')
    
    # If not in GET parameters, try to get from session
    if not association_id:
        association_id = request.session.get('selected_association_id')
        logger.debug(f"Using association_id {association_id} from session")
    
    if not tax_year:
        tax_year = request.session.get('selected_tax_year')
        logger.debug(f"Using tax_year {tax_year} from session")
    
    association = None
    financial_instance = None
    
    if association_id and tax_year:
        association = get_object_or_404(Association, id=association_id)
        financial_instance, created = Financial.objects.get_or_create(
            association=association,
            tax_year=tax_year
        )
        
        # Store in session
        request.session['selected_association_id'] = association_id
        request.session['selected_tax_year'] = int(tax_year)

    if request.method == 'POST':
        form = FinancialForm(request.POST, instance=financial_instance)
        if form.is_valid():
            financial = form.save()
            
            # Store association and tax year in session
            request.session['selected_association_id'] = str(financial.association.id)
            request.session['selected_tax_year'] = financial.tax_year
            
            messages.success(request, 'Financial information saved successfully.')
            return redirect('index')
    else:
        form = FinancialForm(instance=financial_instance)

    context = {
        'form': form,
        'association': association,
        'tax_year': tax_year,
        'is_update': financial_instance is not None and not created if financial_instance else False
    }
    return render(request, 'tax_form/create_financial.html', context)