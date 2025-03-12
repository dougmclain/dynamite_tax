from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from azure.storage.blob import BlobServiceClient
from ..models import Association, Financial, Extension, CompletedTaxReturn
from ..tax_calculations import (
    calculate_total_exempt_income, calculate_total_other_income, calculate_gross_income,
    calculate_other_deductions, calculate_total_tax, calculate_expenses_lineC,
    calculate_total_payments, calculate_amount_owed, calculate_overpayment
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AssociationView(LoginRequiredMixin, View):
    template_name = 'tax_form/association.html'

    def get(self, request):
        associations = Association.objects.all().order_by('association_name')
        
        # Get association ID from URL parameters or session
        selected_association_id = request.GET.get('association_id')
        if not selected_association_id:
            # Try to get from session if not in URL
            selected_association_id = request.session.get('selected_association_id')
            logger.debug(f"Retrieved association_id {selected_association_id} from session")
        
        # Get tax year from URL parameters or session
        tax_year_param = request.GET.get('tax_year')
        
        if tax_year_param and tax_year_param.strip():
            selected_tax_year = int(tax_year_param)
            # Save to session
            request.session['selected_tax_year'] = selected_tax_year
        else:
            # Try to get from session, or use current year as default
            selected_tax_year = request.session.get('selected_tax_year', datetime.now().year)
            logger.debug(f"Retrieved tax_year {selected_tax_year} from session")

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

            # Store in session if not already there
            request.session['selected_association_id'] = selected_association_id

            # Add new association information
            context['association_info'] = {
                'name': selected_association.association_name,
                'mailing_address': selected_association.mailing_address,
                'city': selected_association.city,
                'state': selected_association.state,
                'zipcode': selected_association.zipcode,
                'ein': selected_association.ein,
                'formation_date': selected_association.formation_date,
                'association_type': selected_association.get_association_type_display(),
                'contact_name': f"{selected_association.contact_first_name} {selected_association.contact_last_name}",
                'contact_email': selected_association.contact_email,
            }

            financial_data = Financial.objects.filter(
                association=selected_association,
                tax_year=selected_tax_year
            ).first()

            if financial_data:
                context['financial_data'] = financial_data
                extension = Extension.objects.filter(financial=financial_data).first()
                completed_tax_return = CompletedTaxReturn.objects.filter(financial=financial_data).first()

                # Create Azure connection for file checks
                azure_connection = None
                try:
                    connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
                    azure_connection = BlobServiceClient.from_connection_string(connection_string)
                except Exception as azure_error:
                    logger.error(f"Error connecting to Azure: {str(azure_error)}", exc_info=True)

                # Process extension data
                if extension:
                    if extension.form_7004 and extension.form_7004.name:
                        file_path = extension.form_7004.name
                        logger.debug(f"Checking for extension file at path: {file_path}")
                        
                        # Generate direct URL
                        file_url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER}/{file_path}"
                        logger.debug(f"Generated URL for extension file: {file_url}")
                        
                        # Check if blob exists directly with Azure
                        file_exists = False
                        if azure_connection:
                            try:
                                blob_client = azure_connection.get_blob_client(container=settings.AZURE_CONTAINER, blob=file_path)
                                properties = blob_client.get_blob_properties()
                                logger.debug(f"Extension file exists with properties: {properties.last_modified}")
                                file_exists = True
                            except Exception as blob_error:
                                logger.warning(f"Extension file not found in Azure: {str(blob_error)}")
                                file_exists = False
                        
                        if file_exists:
                            context['extension_data'] = extension
                        else:
                            logger.warning(f"Extension file does not exist: {file_path}")
                            extension.form_7004 = None
                            extension.save()
                            context['extension_data'] = extension
                    else:
                        context['extension_data'] = extension

                # Process completed tax return data
                if completed_tax_return:
                    if completed_tax_return.tax_return_pdf and completed_tax_return.tax_return_pdf.name:
                        file_path = completed_tax_return.tax_return_pdf.name
                        logger.debug(f"Checking for tax return file at path: {file_path}")
                        
                        # Generate direct URL
                        file_url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER}/{file_path}"
                        logger.debug(f"Generated URL for tax return file: {file_url}")
                        
                        # Check if blob exists directly with Azure
                        file_exists = False
                        if azure_connection:
                            try:
                                blob_client = azure_connection.get_blob_client(container=settings.AZURE_CONTAINER, blob=file_path)
                                properties = blob_client.get_blob_properties()
                                logger.debug(f"Tax return file exists with properties: {properties.last_modified}")
                                file_exists = True
                            except Exception as blob_error:
                                logger.warning(f"Tax return file not found in Azure: {str(blob_error)}")
                                file_exists = False
                        
                        if file_exists:
                            context['completed_tax_return_data'] = completed_tax_return
                        else:
                            logger.warning(f"Tax return file does not exist: {file_path}")
                            completed_tax_return.tax_return_pdf = None
                            completed_tax_return.save()
                            context['completed_tax_return_data'] = completed_tax_return
                    else:
                        context['completed_tax_return_data'] = completed_tax_return

                # Calculate financial information
                context['total_exempt_income'] = calculate_total_exempt_income(financial_data)
                context['expenses_lineC'] = calculate_expenses_lineC(financial_data)
                context['total_taxable_income'] = calculate_total_other_income(financial_data)
                context['gross_income'] = calculate_gross_income(financial_data)

                context['other_deductions'] = calculate_other_deductions(financial_data)
                context['total_tax'] = calculate_total_tax(financial_data)
                context['total_payments'] = calculate_total_payments(financial_data)
                context['amount_owed'] = calculate_amount_owed(context['total_tax'], context['total_payments'])
                context['overpayment'] = calculate_overpayment(context['total_tax'], context['total_payments'])

                # Taxable income breakdown
                context['taxable_income'] = {
                    'interest': financial_data.interest,
                    'dividends': financial_data.dividends,
                    'rentals': financial_data.rentals,
                    'non_exempt_income1': financial_data.non_exempt_income_amount1,
                    'non_exempt_income2': financial_data.non_exempt_income_amount2,
                    'non_exempt_income3': financial_data.non_exempt_income_amount3,
                }

            # Calculate due dates
            context['tax_return_due_date'] = selected_association.get_tax_return_due_date(selected_tax_year)
            context['extended_due_date'] = selected_association.get_extended_due_date(selected_tax_year)

        return render(request, self.template_name, context)