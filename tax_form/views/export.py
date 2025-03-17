# Update tax_form/views/export.py

from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin   
from django.http import HttpResponse
from django.utils import timezone
from ..models import Association, Financial, CompletedTaxReturn, ManagementCompany, AssociationFilingStatus
import csv
import logging

logger = logging.getLogger(__name__)

class ExportAssociationsView(LoginRequiredMixin, View):
    """View to export association data for a specific management company, filtered by filing status"""
    
    def get(self, request):
        # Get parameters from the request
        management_company_id = request.GET.get('management_company')
        tax_year = request.GET.get('tax_year')
        export_format = request.GET.get('format', 'html')  # Default to HTML
        
        if not tax_year:
            # Default to current year
            tax_year = timezone.now().year
        else:
            tax_year = int(tax_year)
        
        # Check if a specific management company is selected
        if not management_company_id or management_company_id == 'all':
            # Redirect back to dashboard with an error message if no specific company is selected
            messages.error(request, "Please select a specific management company before exporting.")
            return redirect(f'/dashboard/?tax_year={tax_year}&management_company=all')
        
        # Define the query for associations
        query = Association.objects.all().order_by('association_name')
        management_company_name = "All Companies"
        
        # Filter by management company
        if management_company_id == 'self':
            query = query.filter(is_self_managed=True)
            management_company_name = "Self-Managed"
        else:
            # Filter for specific management company
            try:
                company = ManagementCompany.objects.get(id=management_company_id)
                query = query.filter(management_company=company)
                management_company_name = company.name
            except ManagementCompany.DoesNotExist:
                messages.error(request, "Selected management company not found.")
                return redirect(f'/dashboard/?tax_year={tax_year}')
        
        # Get associations with their tax return status
        associations_data = []
        
        # Counter for numbering only included associations
        idx = 1
        
        for association in query:
            # Check if this association is marked for filing in the selected tax year
            filing_status, created = AssociationFilingStatus.objects.get_or_create(
                association=association,
                tax_year=tax_year,
                defaults={'prepare_return': True}
            )
            
            # Skip associations not marked for filing
            if not filing_status.prepare_return:
                continue
            
            # Get financial record for this tax year
            financial = Financial.objects.filter(
                association=association,
                tax_year=tax_year
            ).first()
            
            # Get tax return status
            completed_tax_return = None
            sent_status = "Not Sent"
            filed_status = "Not Filed"
            
            if financial:
                completed_tax_return = CompletedTaxReturn.objects.filter(
                    financial=financial
                ).first()
                
                if completed_tax_return:
                    if completed_tax_return.sent_for_signature:
                        sent_date = ""
                        if completed_tax_return.sent_date:
                            sent_date = f" ({completed_tax_return.sent_date.strftime('%m/%d/%Y')})"
                        sent_status = f"Sent{sent_date}"
                    
                    if completed_tax_return.return_filed:
                        filed_date = ""
                        if completed_tax_return.date_prepared:
                            filed_date = f" ({completed_tax_return.date_prepared.strftime('%m/%d/%Y')})"
                        
                        status_map = {
                            'not_filed': 'Not Filed',
                            'filed_by_dynamite': 'Filed by Dynamite',
                            'filed_by_association': 'Filed by Association'
                        }
                        filed_status = f"{status_map.get(completed_tax_return.filing_status, 'Filed')}{filed_date}"
            
            # Determine management info
            if association.is_self_managed:
                management_info = "Self-Managed"
            elif association.management_company:
                management_info = association.management_company.name
            else:
                management_info = "Unspecified"
            
            # Add to our data list with the current index
            associations_data.append({
                'number': idx,
                'name': association.association_name,
                'ein': association.ein,
                'management': management_info,
                'sent_status': sent_status,
                'filed_status': filed_status,
                'invoiced': 'Yes' if filing_status.invoiced else 'No'
            })
            
            # Increment the index only for associations we're including
            idx += 1
        
        # If no associations match our criteria, show a message
        if not associations_data:
            messages.warning(request, f"No associations marked for filing found for {management_company_name} in {tax_year}.")
            return redirect(f'/dashboard/?tax_year={tax_year}&management_company={management_company_id}')
        
        # Handle different export formats
        if export_format == 'csv':
            # Create a CSV response
            filename = f"associations_to_file_{management_company_name.replace(' ', '_')}_{tax_year}.csv"
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Create CSV writer directly using response
            writer = csv.writer(response)
            
            # Write header
            writer.writerow(['#', 'Association Name', 'EIN', 'Management', 'Tax Year', 'Return Sent Status', 'Return Filed Status', 'Invoiced'])
            
            # Write data
            for assoc in associations_data:
                writer.writerow([
                    assoc['number'],
                    assoc['name'],
                    assoc['ein'],
                    assoc['management'],
                    tax_year,
                    assoc['sent_status'],
                    assoc['filed_status'],
                    assoc['invoiced']
                ])
            
            return response
        else:
            # Return HTML view
            context = {
                'associations_data': associations_data,
                'tax_year': tax_year,
                'management_company_name': management_company_name,
                'filing_only': True
            }
            return render(request, 'tax_form/export_associations.html', context)