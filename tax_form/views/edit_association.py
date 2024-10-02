from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from ..forms import AssociationForm
from ..models import Association

class EditAssociationView(View):
    template_name = 'tax_form/edit_association.html'

    def get(self, request, association_id):
        association = get_object_or_404(Association, id=association_id)
        form = AssociationForm(instance=association)
        tax_year = request.GET.get('tax_year', '')  # Get the tax_year from query parameters
        context = {
            'form': form,
            'association': association,
            'tax_year': tax_year,
        }
        return render(request, self.template_name, context)

    def post(self, request, association_id):
        association = get_object_or_404(Association, id=association_id)
        form = AssociationForm(request.POST, instance=association)
        tax_year = request.POST.get('tax_year', '')  # Get the tax_year from the form
        if form.is_valid():
            form.save()
            messages.success(request, f'Association "{association.association_name}" updated successfully.')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")
        context = {
            'form': form,
            'association': association,
            'tax_year': tax_year,
        }
        return render(request, self.template_name, context)