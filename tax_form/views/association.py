from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from ..models import Association, Financial, Extension
from ..forms import AssociationForm
from datetime import datetime

class AssociationView(View):
    template_name = 'tax_form/association.html'

class AssociationView(View):
    template_name = 'tax_form/association.html'

    def get(self, request):
        associations = Association.objects.all().order_by('association_name')
        selected_association_id = request.GET.get('association_id')
        selected_tax_year = int(request.GET.get('tax_year', datetime.now().year))

        context = {
            'associations': associations,
            'selected_association': None,
            'financial_data': None,
            'extension_data': None,
            'tax_return_due_date': None,
            'extended_due_date': None,
            'selected_tax_year': selected_tax_year,
            'available_tax_years': range(datetime.now().year - 5, datetime.now().year + 1),
        }

        if selected_association_id:
            selected_association = get_object_or_404(Association, id=selected_association_id)
            context['selected_association'] = selected_association

            # Get financial data for the selected tax year
            financial_data = Financial.objects.filter(
                association=selected_association,
                tax_year=selected_tax_year
            ).first()
            context['financial_data'] = financial_data

            # Get extension data for the selected tax year
            if financial_data:
                extension_data = Extension.objects.filter(
                    financial=financial_data
                ).first()
                context['extension_data'] = extension_data

            # Calculate due dates
            context['tax_return_due_date'] = selected_association.get_tax_return_due_date(selected_tax_year)
            context['extended_due_date'] = selected_association.get_extended_due_date(selected_tax_year)

        return render(request, self.template_name, context)

