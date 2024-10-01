from django.views import View
from django.shortcuts import render
from ..models import Association, Financial, Extension, CompletedTaxReturn
from django.utils import timezone
from django.db.models import Min, Max

class DashboardView(View):
    template_name = 'tax_form/dashboard.html'

    def get(self, request):
        # Get the range of available tax years
        year_range = Financial.objects.aggregate(Min('tax_year'), Max('tax_year'))
        min_year = year_range['tax_year__min'] or timezone.now().year
        max_year = max(year_range['tax_year__max'] or timezone.now().year, timezone.now().year)
        available_years = range(max_year, min_year - 1, -1)  # Reverse order, include future year

        # Get the selected year from the query parameters, default to the current year
        selected_year = int(request.GET.get('tax_year', timezone.now().year))

        associations = Association.objects.all().order_by('association_name')
        dashboard_data = []

        for association in associations:
            financial = Financial.objects.filter(association=association, tax_year=selected_year).first()
            extension = Extension.objects.filter(financial=financial).first() if financial else None
            completed_tax_return = CompletedTaxReturn.objects.filter(financial=financial).first() if financial else None

            dashboard_data.append({
                'association': association,
                'fiscal_year_end': association.get_fiscal_year_end(selected_year),
                'tax_return_due_date': association.get_tax_return_due_date(selected_year),
                'extended_due_date': association.get_extended_due_date(selected_year),
                'extension_filed': extension.filed if extension else False,
                'extension_filed_date': extension.filed_date if extension and extension.filed else None,
                'tax_return_filed': completed_tax_return.return_filed if completed_tax_return else False,
                'tax_return_prepared_date': completed_tax_return.date_prepared if completed_tax_return and completed_tax_return.return_filed else None,
            })

        context = {
            'dashboard_data': dashboard_data,
            'selected_year': selected_year,
            'available_years': available_years,
        }
        return render(request, self.template_name, context)