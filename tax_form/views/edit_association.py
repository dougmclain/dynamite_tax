from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from ..forms import AssociationForm
from ..models import Association

class EditAssociationView(View):
    template_name = 'tax_form/edit_association.html'

    def get(self, request, association_id):
        association = get_object_or_404(Association, id=association_id)
        form = AssociationForm(instance=association)
        context = {
            'form': form,
            'association': association,
        }
        return render(request, self.template_name, context)

    def post(self, request, association_id):
        association = get_object_or_404(Association, id=association_id)
        form = AssociationForm(request.POST, instance=association)
        if form.is_valid():
            form.save()
            messages.success(request, f'Association "{association.association_name}" updated successfully.')
            return redirect('association')  # Redirect to the association detail page
        context = {
            'form': form,
            'association': association,
        }
        return render(request, self.template_name, context)