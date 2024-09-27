from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import Association
from ..forms import AssociationForm

def create_association(request):
    """View for creating a new association."""
    if request.method == 'POST':
        form = AssociationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Association created successfully.')
            return redirect('create_association')
    else:
        form = AssociationForm()

    associations = Association.objects.all().order_by('-formation_date')
    
    context = {
        'form': form,
        'associations': associations,
    }
    return render(request, 'tax_form/create_association.html', context)