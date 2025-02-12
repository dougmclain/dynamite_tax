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

class AssociationView(LoginRequiredMixin, View):
    template_name = 'tax_form/association.html'

    def get(self, request):
        associations = Association.objects.all().order_by('association_name')
        selected_association_id = request.GET.get('association_id')
        
        # Handle the case where tax_year might be empty or not present
        tax_year_param = request.GET.get('tax_year')
        if tax_year_param and tax_year_param.strip():
            selected_tax_year = int(tax_year_param)
        else:
            selected_tax_year = datetime.now().year

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
                context['extension_data'] = Extension.objects.filter(financial=financial_data).first()
                context['completed_tax_return_data'] = CompletedTaxReturn.objects.filter(financial=financial_data).first()

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