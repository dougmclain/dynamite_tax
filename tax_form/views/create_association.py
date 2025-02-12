from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from ..models import Association
from ..forms import AssociationForm

class CreateAssociationView(LoginRequiredMixin, View):
    template_name = 'tax_form/create_association.html'

    def get(self, request):
        form = AssociationForm()
        associations = Association.objects.all().order_by('-formation_date')
        context = {
            'form': form,
            'associations': associations,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = AssociationForm(request.POST)
        if form.is_valid():
            association = form.save()
            messages.success(request, f'Association "{association.association_name}" created successfully.')
            return redirect('association')
        
        associations = Association.objects.all().order_by('-formation_date')
        context = {
            'form': form,
            'associations': associations,
        }
        return render(request, self.template_name, context)

def create_association(request):
    """View for creating a new association."""
    if request.method == 'POST':
        form = AssociationForm(request.POST)
        if form.is_valid():
            association = form.save()
            messages.success(request, f'Association "{association.association_name}" created successfully.')
            return redirect('association')
    else:
        form = AssociationForm()

    associations = Association.objects.all().order_by('-formation_date')
    
    context = {
        'form': form,
        'associations': associations,
    }
    return render(request, 'tax_form/create_association.html', context)