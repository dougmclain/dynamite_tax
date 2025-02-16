from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin   
from ..models import Association, Financial, Extension, CompletedTaxReturn
from django.utils import timezone
from django.db.models import Min, Max, Count, Q
import logging

logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, View):
    template_name = 'tax_form/dashboard.html'

    def get(self, request):
        year_range = Financial.objects.aggregate(Min('tax_year'), Max('tax_year'))
        min_year = year_range['tax_year__min'] or timezone.now().year
        max_year = max(year_range['tax_year__max'] or timezone.now().year, timezone.now().year)
        available_years = range(max_year, min_year - 2, -1)

        # Get tax year from URL, session, or default to current year
        tax_year_param = request.GET.get('tax_year')
        if tax_year_param and tax_year_param.strip():
            selected_year = int(tax_year_param)
            # Save to session
            request.session['selected_tax_year'] = selected_year
            logger.debug(f"Setting selected_tax_year in session to: {selected_year}")
        else:
            # Try to get from session, otherwise use current year
            selected_year = request.session.get('selected_tax_year')
            if not selected_year:
                # If no year in session, use current year
                selected_year = timezone.now().year
                request.session['selected_tax_year'] = selected_year
            logger.debug(f"Using selected_tax_year from session: {selected_year}")

        associations = Association.objects.all().order_by('association_name')
        total_associations = associations.count()

        financials = Financial.objects.filter(tax_year=selected_year)
        filed_returns = CompletedTaxReturn.objects.filter(
            financial__tax_year=selected_year, 
            return_filed=True
        ).count()
        unfiled_returns = total_associations - filed_returns

        dashboard_data = []

        for association in associations:
            financial = financials.filter(association=association).first()
            extension = Extension.objects.filter(financial=financial).first() if financial else None
            completed_tax_return = CompletedTaxReturn.objects.filter(financial=financial).first() if financial else None

            # Check if files exist before including URLs
            extension_file_url = None
            if extension and extension.form_7004:
                try:
                    if extension.form_7004.storage.exists(extension.form_7004.name):
                        extension_file_url = extension.form_7004.url
                except Exception as e:
                    logger.error(f"Error checking extension file: {e}")

            tax_return_file_url = None
            if completed_tax_return and completed_tax_return.tax_return_pdf:
                try:
                    if completed_tax_return.tax_return_pdf.storage.exists(completed_tax_return.tax_return_pdf.name):
                        tax_return_file_url = completed_tax_return.tax_return_pdf.url
                except Exception as e:
                    logger.error(f"Error checking tax return file: {e}")

            dashboard_data.append({
                'association': association,
                'fiscal_year_end': association.get_fiscal_year_end(selected_year),
                'extension_filed': extension.filed if extension else False,
                'extension_filed_date': extension.filed_date if extension and extension.filed else None,
                'extension_file_url': extension_file_url,
                'tax_return_filed': completed_tax_return.return_filed if completed_tax_return else False,
                'tax_return_prepared_date': completed_tax_return.date_prepared if completed_tax_return and completed_tax_return.return_filed else None,
                'tax_return_file_url': tax_return_file_url,
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