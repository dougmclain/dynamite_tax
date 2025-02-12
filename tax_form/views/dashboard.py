from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin   
from ..models import Association, Financial, Extension, CompletedTaxReturn
from django.utils import timezone
from django.db.models import Min, Max, Count, Q

class DashboardView(LoginRequiredMixin, View):
    template_name = 'tax_form/dashboard.html'

    def get(self, request):
        year_range = Financial.objects.aggregate(Min('tax_year'), Max('tax_year'))
        min_year = year_range['tax_year__min'] or timezone.now().year
        max_year = max(year_range['tax_year__max'] or timezone.now().year, timezone.now().year)
        available_years = range(max_year, min_year - 2, -1)

        selected_year = int(request.GET.get('tax_year', timezone.now().year))

        associations = Association.objects.all().order_by('association_name')
        total_associations = associations.count()

        financials = Financial.objects.filter(tax_year=selected_year)
        filed_returns = CompletedTaxReturn.objects.filter(financial__tax_year=selected_year, return_filed=True).count()
        unfiled_returns = total_associations - filed_returns

        dashboard_data = []

        for association in associations:
            financial = financials.filter(association=association).first()
            extension = Extension.objects.filter(financial=financial).first() if financial else None
            completed_tax_return = CompletedTaxReturn.objects.filter(financial=financial).first() if financial else None

            dashboard_data.append({
                'association': association,
                'fiscal_year_end': association.get_fiscal_year_end(selected_year),
                'extension_filed': extension.filed if extension else False,
                'extension_filed_date': extension.filed_date if extension and extension.filed else None,
                'extension_file_url': extension.form_7004.url if extension and extension.form_7004 else None,
                'tax_return_filed': completed_tax_return.return_filed if completed_tax_return else False,
                'tax_return_prepared_date': completed_tax_return.date_prepared if completed_tax_return and completed_tax_return.return_filed else None,
                'tax_return_file_url': completed_tax_return.tax_return_pdf.url if completed_tax_return and completed_tax_return.tax_return_pdf else None,
            })

        context = {
            'dashboard_data': dashboard_data,
            'selected_year': selected_year,
            'available_years': available_years,
            'total_associations': total_associations,
            'filed_returns': filed_returns,
            'unfiled_returns': unfiled_returns,
        }
        return render(request, self.template_name, context)