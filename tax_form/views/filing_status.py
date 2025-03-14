# Create this file at: tax_form/views/filing_status.py

from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from ..forms import AssociationFilingStatusForm
from ..models import Association, AssociationFilingStatus
import logging

logger = logging.getLogger(__name__)

class EditFilingStatusView(LoginRequiredMixin, View):
    template_name = 'tax_form/edit_filing_status.html'

    def get(self, request, association_id, tax_year):
        association = get_object_or_404(Association, id=association_id)
        
        # Get or create filing status for this association and year
        filing_status, created = AssociationFilingStatus.objects.get_or_create(
            association=association,
            tax_year=tax_year,
            defaults={'prepare_return': True}
        )
        
        # Store in session
        request.session['selected_association_id'] = str(association_id)
        request.session['selected_tax_year'] = int(tax_year)
        
        form = AssociationFilingStatusForm(instance=filing_status)
        
        context = {
            'form': form,
            'association': association,
            'tax_year': tax_year,
            'filing_status': filing_status,
        }
        return render(request, self.template_name, context)

    def post(self, request, association_id, tax_year):
        association = get_object_or_404(Association, id=association_id)
        
        # Get or create filing status for this association and year
        filing_status, created = AssociationFilingStatus.objects.get_or_create(
            association=association,
            tax_year=tax_year,
            defaults={'prepare_return': True}
        )
        
        form = AssociationFilingStatusForm(request.POST, instance=filing_status)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Filing status for {association.association_name} - {tax_year} updated successfully.')
            
            # Redirect back to association page or dashboard
            return_url = request.GET.get('next', reverse('dashboard'))
            return redirect(f"{return_url}?tax_year={tax_year}")
        
        context = {
            'form': form,
            'association': association,
            'tax_year': tax_year,
            'filing_status': filing_status,
        }
        return render(request, self.template_name, context)