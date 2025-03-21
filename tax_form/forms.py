from django import forms
from .models import Association, Financial, Preparer, Extension, CompletedTaxReturn, EngagementLetter, AssociationFilingStatus, ManagementCompany
from django.forms.widgets import NumberInput, TextInput
import logging

logger = logging.getLogger(__name__)

class TaxFormSelectionForm(forms.Form):
    association = forms.ModelChoiceField(queryset=Association.objects.all(), empty_label=None)
    tax_year = forms.ChoiceField(choices=[])
    preparer = forms.ModelChoiceField(queryset=Preparer.objects.all(), empty_label="Select a Preparer", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['association'].widget.attrs['class'] = 'form-select'
        self.fields['tax_year'].widget.attrs['class'] = 'form-select'
        self.fields['preparer'].widget.attrs['class'] = 'form-select'

        logger.debug(f"Form initialized with data: {self.data}")
        logger.debug(f"Form initialized with initial: {self.initial}")

        # Check for initial data for association, which can come from session
        association_id = None
        if self.initial and 'association' in self.initial:
            association_id = self.initial['association']
        elif self.data and 'association' in self.data:
            association_id = self.data.get('association')

        if association_id:
            # Load tax years for this association
            financial_years = Financial.objects.filter(
                association_id=association_id
            ).values_list('tax_year', flat=True).distinct().order_by('-tax_year')
            self.fields['tax_year'].choices = [(str(year), str(year)) for year in financial_years]
            logger.debug(f"Tax years for association {association_id}: {self.fields['tax_year'].choices}")
        else:
            # If no association found, get any available tax year
            if Association.objects.exists():
                # Get the first association's tax years
                default_association = Association.objects.first()
                financial_years = Financial.objects.filter(
                    association_id=default_association.id
                ).values_list('tax_year', flat=True).distinct().order_by('-tax_year')
                self.fields['tax_year'].choices = [(str(year), str(year)) for year in financial_years]
            else:
                self.fields['tax_year'].choices = []
            logger.debug("Using default tax year choices or empty list")

class AssociationForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = [
            'association_name', 'mailing_address', 'city', 'state', 'zipcode', 
            'zoned', 'ein', 'formation_date', 'association_type',
            'fiscal_year_end_month',
            'contact_first_name', 'contact_last_name', 'contact_email',
            'is_self_managed', 'management_company'
        ]
        widgets = {
            'formation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'association_type': forms.Select(attrs={'class': 'form-select'}),
            'fiscal_year_end_month': forms.Select(attrs={'class': 'form-select'}),
            'management_company': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['zoned', 'is_self_managed']:
                self.fields[field].widget.attrs['class'] = 'form-control'
        
        self.fields['zoned'].widget.attrs['class'] = 'form-check-input'
        self.fields['is_self_managed'].widget.attrs['class'] = 'form-check-input'

        self.fields['contact_first_name'].widget.attrs['placeholder'] = 'First Name'
        self.fields['contact_last_name'].widget.attrs['placeholder'] = 'Last Name'
        self.fields['contact_email'].widget.attrs['placeholder'] = 'Email'
        self.fields['fiscal_year_end_month'].label = 'Fiscal Year End Month'
        
        # Add an empty option for management company field
        self.fields['management_company'].empty_label = "Select a management company"
        
        # Add help text for the management fields
        self.fields['is_self_managed'].help_text = "Uncheck if the association is managed by a management company"
        self.fields['management_company'].help_text = "Select the management company if the association is not self-managed"

class DollarNumberInput(NumberInput):
    template_name = 'tax_form/dollar_number_input.html'

class FinancialForm(forms.ModelForm):
    class Meta:
        model = Financial
        fields = '__all__'
        widgets = {
            'member_assessments': TextInput(attrs={'class': 'dollar-input'}),
            'capital_contribution': TextInput(attrs={'class': 'dollar-input'}),
            'moving_fees': TextInput(attrs={'class': 'dollar-input'}),
            'utilities': TextInput(attrs={'class': 'dollar-input'}),
            'late_fees': TextInput(attrs={'class': 'dollar-input'}),
            'fines': TextInput(attrs={'class': 'dollar-input'}),
            'other_exempt_income': TextInput(attrs={'class': 'dollar-input'}),
            'total_expenses': TextInput(attrs={'class': 'dollar-input'}),
            'interest': TextInput(attrs={'class': 'dollar-input'}),
            'dividends': TextInput(attrs={'class': 'dollar-input'}),
            'rentals': TextInput(attrs={'class': 'dollar-input'}),
            'non_exempt_income_amount1': TextInput(attrs={'class': 'dollar-input'}),
            'non_exempt_income_amount2': TextInput(attrs={'class': 'dollar-input'}),
            'non_exempt_income_amount3': TextInput(attrs={'class': 'dollar-input'}),
            'tax_preparation': TextInput(attrs={'class': 'dollar-input'}),
            'management_fees': TextInput(attrs={'class': 'dollar-input'}),
            'administration_fees': TextInput(attrs={'class': 'dollar-input'}),
            'audit_fees': TextInput(attrs={'class': 'dollar-input'}),
            'allocated_rental_expenses': TextInput(attrs={'class': 'dollar-input'}),
            'non_exempt_expense_amount1': TextInput(attrs={'class': 'dollar-input'}),
            'non_exempt_expense_amount2': TextInput(attrs={'class': 'dollar-input'}),
            'non_exempt_expense_amount3': TextInput(attrs={'class': 'dollar-input'}),
            'prior_year_over_payment': TextInput(attrs={'class': 'dollar-input'}),
            'extension_payment': TextInput(attrs={'class': 'dollar-input'}),
            'estimated_payment': TextInput(attrs={'class': 'dollar-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            for field_name, field in self.fields.items():
                if isinstance(field.widget, TextInput) and field.widget.attrs.get('class') == 'dollar-input':
                    field.widget.attrs['data-original-value'] = getattr(self.instance, field_name) or ''
                    

class ExtensionForm(forms.ModelForm):
    class Meta:
        model = Extension
        fields = ['filed', 'filed_date', 'tentative_tax', 'total_payments']
        widgets = {
            'filed_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'tentative_tax': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'total_payments': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['filed'].widget.attrs['class'] = 'form-check-input'
        self.fields['filed'].required = False
        self.fields['filed_date'].required = False
        self.fields['tentative_tax'].required = False
        self.fields['total_payments'].required = False
        
# Fix the indentation of EngagementLetterForm - it should not be nested inside ExtensionForm
class EngagementLetterForm(forms.ModelForm):
    class Meta:
        model = EngagementLetter
        fields = ['association', 'tax_year', 'price']
        widgets = {
            'association': forms.Select(attrs={'class': 'form-select'}),
            'tax_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '50'}),
        }
        
class AssociationFilingStatusForm(forms.ModelForm):
    class Meta:
        model = AssociationFilingStatus
        fields = ['prepare_return', 'not_filing_reason', 'invoiced']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the not_filing_reason field not required
        self.fields['not_filing_reason'].required = False
        
        # Add classes to form elements
        self.fields['prepare_return'].widget.attrs['class'] = 'form-check-input'
        self.fields['invoiced'].widget.attrs['class'] = 'form-check-input'
        self.fields['not_filing_reason'].widget.attrs['class'] = 'form-control'
        
# Add to tax_form/forms.py

class ManagementCompanyForm(forms.ModelForm):
    class Meta:
        model = ManagementCompany
        fields = [
            'name', 'contact_person', 'email', 'phone',
            'address', 'city', 'state', 'zipcode',
            'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

        # Add placeholders for common fields
        self.fields['name'].widget.attrs['placeholder'] = 'Management Company Name'
        self.fields['contact_person'].widget.attrs['placeholder'] = 'Contact Person'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['phone'].widget.attrs['placeholder'] = 'Phone'