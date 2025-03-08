from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Financial, Association
from ..forms import FinancialForm
from ..utils.session_management import save_selection_to_session, get_selection_from_session

@login_required
def create_financial(request):
    """View for creating or updating financial information."""
    association_id = request.GET.get('association')
    tax_year = request.GET.get('tax_year')
    
    # If we have parameters, save to session
    if association_id or tax_year:
        save_selection_to_session(
            request,
            association_id=association_id,
            tax_year=tax_year
        )
    # If not, try to get from session
    elif not association_id or not tax_year:
        session_association_id, session_tax_year = get_selection_from_session(request)
        
        if not association_id and session_association_id:
            association_id = session_association_id
            
        if not tax_year and session_tax_year:
            tax_year = session_tax_year
    
    if association_id and tax_year:
        association = get_object_or_404(Association, id=association_id)
        financial_instance, created = Financial.objects.get_or_create(
            association=association,
            tax_year=tax_year
        )
    else:
        association = None
        financial_instance = None

    if request.method == 'POST':
        form = FinancialForm(request.POST, instance=financial_instance)
        if form.is_valid():
            financial = form.save()
            # Save the selection to session
            save_selection_to_session(
                request,
                association_id=financial.association.id,
                tax_year=financial.tax_year
            )
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