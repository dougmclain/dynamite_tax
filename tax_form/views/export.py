# Create a new file tax_form/views/export.py

from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin   
from django.http import HttpResponse
from django.utils import timezone
from ..models import Association, Financial, CompletedTaxReturn, ManagementCompany
import csv
import logging
from io import StringIO

logger = logging.getLogger(__name__)

class ExportAssociationsView(LoginRequiredMixin, View):
    """View to export association data for a specific management company"""
    
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
        
        # Define the query for associations
        query = Association.objects.all().order_by('association_name')
        management_company_name = "All Companies"
        
        # Filter by management company if specified
        if management_company_id:
            if management_company_id == 'self':
                query = query.filter(is_self_managed=True)
                management_company_name = "Self-Managed"
            elif management_company_id != 'all':
                # Filter for specific management company
                try:
                    company = ManagementCompany.objects.get(id=management_company_id)
                    query = query.filter(management_company=company)
                    management_company_name = company.name
                except ManagementCompany.DoesNotExist:
                    pass
        
        # Get associations with their tax return status
        associations_data = []
        for idx, association in enumerate(query, 1):
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
            
            # Add to our data list
            associations_data.append({
                'number': idx,
                'name': association.association_name,
                'ein': association.ein,
                'management': management_info,
                'sent_status': sent_status,
                'filed_status': filed_status
            })
        
        # Handle different export formats
        if export_format == 'csv':
            # Create a CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="associations_{management_company_name.replace(" ", "_")}_{tax_year}.csv"'
            
            # Create CSV writer
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            
            # Write header
            writer.writerow(['#', 'Association Name', 'EIN', 'Management', 'Tax Year', 'Return Sent Status', 'Return Filed Status'])
            
            # Write data
            for assoc in associations_data:
                writer.writerow([
                    assoc['number'],
                    assoc['name'],
                    assoc['ein'],
                    assoc['management'],
                    tax_year,
                    assoc['sent_status'],
                    assoc['filed_status']
                ])
            
            # Get the CSV content and write to response
            response.write(csv_buffer.getvalue())
            return response
        else:
            # Return HTML view
            context = {
                'associations_data': associations_data,
                'tax_year': tax_year,
                'management_company_name': management_company_name
            }
            return render(request, 'tax_form/export_associations.html', context)