from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
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

                # Process extension data
                # Process extension data
                if extension:
                    if extension.form_7004:
                        file_path = extension.form_7004.name
                        logger.debug(f"Checking for extension file at path: {file_path}")
                        
                        try:
                            # Try to get the URL first to see if it's generated correctly
                            file_url = extension.form_7004.url
                            logger.debug(f"Generated URL for extension file: {file_url}")
                            
                            # Check if file exists in storage
                            file_exists = extension.form_7004.storage.exists(file_path)
                            logger.debug(f"Extension file exists check result: {file_exists}")
                            
                            if not file_exists:
                                logger.warning(f"Extension file does not exist: {file_path}")
                                
                                # Try an alternative path (with or without media prefix)
                                alt_path = file_path if file_path.startswith('media/') else f"media/{file_path}"
                                logger.debug(f"Trying alternative path: {alt_path}")
                                alt_exists = extension.form_7004.storage.exists(alt_path)
                                logger.debug(f"Alternative path exists: {alt_exists}")
                                
                                if alt_exists:
                                    # If the alternative path works, update the model
                                    logger.info(f"Found extension file at alternative path: {alt_path}")
                                    extension.form_7004.name = alt_path
                                    extension.save()
                                    context['extension_data'] = extension
                                else:
                                    # If file still can't be found, clear the field
                                    logger.warning(f"Could not find extension file at any path, clearing field")
                                    extension.form_7004 = None
                                    extension.save()
                                    context['extension_data'] = extension
                            else:
                                context['extension_data'] = extension
                        except Exception as e:
                            logger.error(f"Error checking extension file: {e}", exc_info=True)
                            context['extension_data'] = extension
                    else:
                        context['extension_data'] = extension
                # Process completed tax return data
# Process completed tax return data
                if completed_tax_return:
                    if completed_tax_return.tax_return_pdf:
                        file_path = completed_tax_return.tax_return_pdf.name
                        logger.debug(f"Checking for tax return file at path: {file_path}")
                        
                        try:
                            # Try to get the URL first to see if it's generated correctly
                            file_url = completed_tax_return.tax_return_pdf.url
                            logger.debug(f"Generated URL for tax return file: {file_url}")
                            
                            # Check if file exists in storage
                            file_exists = completed_tax_return.tax_return_pdf.storage.exists(file_path)
                            logger.debug(f"File exists check result: {file_exists}")
                            
                            if not file_exists:
                                logger.warning(f"Tax return file does not exist: {file_path}")
                                
                                # Try an alternative path (with or without media prefix)
                                alt_path = file_path if file_path.startswith('media/') else f"media/{file_path}"
                                logger.debug(f"Trying alternative path: {alt_path}")
                                alt_exists = completed_tax_return.tax_return_pdf.storage.exists(alt_path)
                                logger.debug(f"Alternative path exists: {alt_exists}")
                                
                                if alt_exists:
                                    # If the alternative path works, update the model
                                    logger.info(f"Found file at alternative path: {alt_path}")
                                    completed_tax_return.tax_return_pdf.name = alt_path
                                    completed_tax_return.save()
                                    context['completed_tax_return_data'] = completed_tax_return
                                else:
                                    # If file still can't be found, clear the field
                                    logger.warning(f"Could not find tax return file at any path, clearing field")
                                    completed_tax_return.tax_return_pdf = None
                                    completed_tax_return.save()
                                    context['completed_tax_return_data'] = completed_tax_return
                            else:
                                context['completed_tax_return_data'] = completed_tax_return
                        except Exception as e:
                            logger.error(f"Error checking tax return file: {e}", exc_info=True)
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