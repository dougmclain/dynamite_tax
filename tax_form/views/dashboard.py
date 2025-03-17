# Update tax_form/views/dashboard.py

from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin   
from ..models import Association, Financial, Extension, CompletedTaxReturn, EngagementLetter, AssociationFilingStatus, ManagementCompany
from django.utils import timezone
from django.db.models import Min, Max, Count, Q, F, Value, BooleanField
from django.db.models.functions import Coalesce
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, View):
    template_name = 'tax_form/dashboard.html'

    def get(self, request):
        # Get tax year range from financial records
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

        # Get management company filter from URL or default to all
        management_company_id = request.GET.get('management_company')
        
        # Get all management companies for the filter dropdown
        management_companies = ManagementCompany.objects.all().order_by('name')

        # Get all associations, applying management company filter if selected
        query = Association.objects.all()
        if management_company_id:
            if management_company_id == 'self':
                # Filter for self-managed associations
                query = query.filter(is_self_managed=True)
            elif management_company_id != 'all':
                # Filter for specific management company
                query = query.filter(management_company_id=management_company_id)
        
        associations = query.order_by('association_name')
        total_associations = associations.count()

        # Get filing statuses for selected year, creating defaults for those that don't exist
        filing_statuses = {}
        for assoc in associations:
            status, created = AssociationFilingStatus.objects.get_or_create(
                association=assoc,
                tax_year=selected_year,
                defaults={'prepare_return': True, 'invoiced': False}
            )
            filing_statuses[assoc.id] = status
        
        # Count associations we'll be preparing returns for
        associations_to_file = sum(1 for status in filing_statuses.values() if status.prepare_return)
        
        # Count tax returns that have been filed
        financials = Financial.objects.filter(tax_year=selected_year)
        filed_returns = CompletedTaxReturn.objects.filter(
            financial__tax_year=selected_year, 
            return_filed=True,
            financial__association__filing_statuses__prepare_return=True,
            financial__association__filing_statuses__tax_year=selected_year
        ).count()
        
        # Count returns sent for signature
        sent_returns = CompletedTaxReturn.objects.filter(
            financial__tax_year=selected_year,
            sent_for_signature=True,
            financial__association__filing_statuses__prepare_return=True,
            financial__association__filing_statuses__tax_year=selected_year
        ).count()
        
        # Calculate unfiled returns (associations we'll file for minus those already filed)
        unfiled_returns = associations_to_file - filed_returns
        
        # Count invoiced associations
        invoiced_associations = AssociationFilingStatus.objects.filter(
            tax_year=selected_year,
            prepare_return=True,
            invoiced=True
        ).count()
        
        # Count uninvoiced associations that we'll prepare returns for
        uninvoiced_associations = associations_to_file - invoiced_associations

        # Get signed engagement letters
        signed_engagement_letters = EngagementLetter.objects.filter(
            tax_year=selected_year,
            status='signed',
            association__filing_statuses__prepare_return=True,
            association__filing_statuses__tax_year=selected_year
        ).count()

        dashboard_data = []

        # Check if Azure Storage is configured
        use_azure = False
        if hasattr(settings, 'USE_AZURE_STORAGE') and settings.USE_AZURE_STORAGE:
            use_azure = True

        for association in associations:
            financial = financials.filter(association=association).first()
            extension = Extension.objects.filter(financial=financial).first() if financial else None
            completed_tax_return = CompletedTaxReturn.objects.filter(financial=financial).first() if financial else None
            engagement_letter = EngagementLetter.objects.filter(association=association, tax_year=selected_year).first()
            filing_status = filing_statuses.get(association.id)
            
            try:
                fiscal_year_end = association.get_fiscal_year_end(selected_year)
            except Exception as e:
                logger.error(f"Error getting fiscal year end: {e}")
                fiscal_year_end = None

            filing_status_display = "Not Filed"
            if completed_tax_return and completed_tax_return.return_filed:
                filing_status_map = {
                    'not_filed': 'Not Filed',
                    'filed_by_dynamite': 'Filed by Dynamite',
                    'filed_by_association': 'Filed by Association'
                }
                filing_status_display = filing_status_map.get(completed_tax_return.filing_status, "Filed")

            # Get management information
            if association.is_self_managed:
                management_info = "Self-Managed"
            elif association.management_company:
                management_info = association.management_company.name
            else:
                management_info = "Unspecified"

            dashboard_data.append({
                'association': association,
                'fiscal_year_end': fiscal_year_end,
                'tax_return_sent_date': completed_tax_return.sent_date if completed_tax_return and completed_tax_return.sent_for_signature else None,
                'tax_return_prepared_date': completed_tax_return.date_prepared if completed_tax_return and completed_tax_return.return_filed else None,
                'tax_return_filed': completed_tax_return.return_filed if completed_tax_return else False,
                'filing_status_display': filing_status_display,
                'engagement_letter': engagement_letter,
                'prepare_return': filing_status.prepare_return if filing_status else True,
                'invoiced': filing_status.invoiced if filing_status else False,
                'not_filing_reason': filing_status.not_filing_reason if filing_status and not filing_status.prepare_return else "",
                'management_info': management_info,
            })

        context = {
            'dashboard_data': dashboard_data,
            'selected_year': selected_year,
            'available_years': available_years,
            'total_associations': total_associations,
            'associations_to_file': associations_to_file,
            'filed_returns': filed_returns,
            'unfiled_returns': unfiled_returns,
            'sent_returns': sent_returns,
            'signed_engagement_letters': signed_engagement_letters,
            'invoiced_associations': invoiced_associations,
            'uninvoiced_associations': uninvoiced_associations,
            'management_companies': management_companies,
            'selected_management_company': management_company_id,
        }
        return render(request, self.template_name, context)