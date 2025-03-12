from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin   
from ..models import Association, Financial, Extension, CompletedTaxReturn, EngagementLetter
from django.utils import timezone
from django.db.models import Min, Max, Count, Q
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, View):
    template_name = 'tax_form/dashboard.html'

    def get(self, request):
        year_range = Financial.objects.aggregate(Min('tax_year'), Max('tax_year'))
        min_year = year_range['tax_year__min'] or timezone.now().year
        max_year = max(year_range['tax_year__max'] or timezone.now().year, timezone.now().year)
        available_years = range(max_year, min_year - 2, -1)

        # Get tax year from URL parameter or session
        selected_year = request.GET.get('tax_year')
        
        if selected_year:
            # If we have a year in the URL, save it to session
            selected_year = int(selected_year)
            request.session['selected_tax_year'] = selected_year
        else:
            # If no year in URL but we have one in session, use that
            selected_year = request.session.get('selected_tax_year')
            if not selected_year:
                # Default to current year if no session data
                selected_year = timezone.now().year
                request.session['selected_tax_year'] = selected_year
            
        # Ensure we're working with an integer
        selected_year = int(selected_year)

        associations = Association.objects.all().order_by('association_name')
        total_associations = associations.count()

        financials = Financial.objects.filter(tax_year=selected_year)
        filed_returns = CompletedTaxReturn.objects.filter(
            financial__tax_year=selected_year, 
            return_filed=True
        ).count()
        unfiled_returns = total_associations - filed_returns

        # Get signed engagement letters
        signed_engagement_letters = EngagementLetter.objects.filter(
            tax_year=selected_year,
            status='signed'
        ).count()

        dashboard_data = []

        for association in associations:
            financial = financials.filter(association=association).first()
            extension = Extension.objects.filter(financial=financial).first() if financial else None
            completed_tax_return = CompletedTaxReturn.objects.filter(financial=financial).first() if financial else None
            engagement_letter = EngagementLetter.objects.filter(association=association, tax_year=selected_year).first()
            
            # Check if files exist and generate direct Azure URLs
            extension_file_url = None
            if extension and extension.form_7004 and extension.form_7004.name:
                extension_file_url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER}/{extension.form_7004.name}"
                
            tax_return_file_url = None
            if completed_tax_return and completed_tax_return.tax_return_pdf and completed_tax_return.tax_return_pdf.name:
                tax_return_file_url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER}/{completed_tax_return.tax_return_pdf.name}"
            
            engagement_letter_url = None
            if engagement_letter and engagement_letter.signed_pdf and engagement_letter.signed_pdf.name:
                engagement_letter_url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER}/{engagement_letter.signed_pdf.name}"

            try:
                fiscal_year_end = association.get_fiscal_year_end(selected_year)
            except Exception as e:
                logger.error(f"Error getting fiscal year end: {e}")
                fiscal_year_end = None

            dashboard_data.append({
                'association': association,
                'fiscal_year_end': fiscal_year_end,
                'extension_filed': extension.filed if extension else False,
                'extension_filed_date': extension.filed_date if extension and extension.filed else None,
                'extension_file_url': extension_file_url,
                'tax_return_filed': completed_tax_return.return_filed if completed_tax_return else False,
                'tax_return_prepared_date': completed_tax_return.date_prepared if completed_tax_return and completed_tax_return.return_filed else None,
                'tax_return_file_url': tax_return_file_url,
                'engagement_letter': engagement_letter,
                'engagement_letter_url': engagement_letter_url,
            })

        context = {
            'dashboard_data': dashboard_data,
            'selected_year': selected_year,
            'available_years': available_years,
            'total_associations': total_associations,
            'filed_returns': filed_returns,
            'unfiled_returns': unfiled_returns,
            'signed_engagement_letters': signed_engagement_letters,
        }
        return render(request, self.template_name, context)