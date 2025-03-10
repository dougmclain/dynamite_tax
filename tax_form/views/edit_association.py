from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from ..forms import AssociationForm
from ..models import Association
import logging

logger = logging.getLogger(__name__)

class EditAssociationView(LoginRequiredMixin, View):
    template_name = 'tax_form/edit_association.html'

    def get(self, request, association_id):
        association = get_object_or_404(Association, id=association_id)
        form = AssociationForm(instance=association)
        
        # Get tax_year from query param or session
        tax_year = request.GET.get('tax_year')
        if not tax_year:
            tax_year = request.session.get('selected_tax_year', '')
            logger.debug(f"Using tax_year {tax_year} from session")
            
        # Store in session
        request.session['selected_association_id'] = str(association_id)
        if tax_year:
            request.session['selected_tax_year'] = int(tax_year)
            
        context = {
            'form': form,
            'association': association,
            'tax_year': tax_year,
        }
        return render(request, self.template_name, context)

    def post(self, request, association_id):
        association = get_object_or_404(Association, id=association_id)
        form = AssociationForm(request.POST, instance=association)
        
        # Get tax_year from the form or session
        tax_year = request.POST.get('tax_year', '')
        if not tax_year:
            tax_year = request.session.get('selected_tax_year', '')
            
        if form.is_valid():
            form.save()
            
            # Maintain association in session
            request.session['selected_association_id'] = str(association_id)
            if tax_year:
                request.session['selected_tax_year'] = int(tax_year)
                
            messages.success(request, f'Association "{association.association_name}" updated successfully.')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")
            
        context = {
            'form': form,
            'association': association,
            'tax_year': tax_year,
        }
        return render(request, self.template_name, context)