from django import forms
from .models import Association, Financial, Preparer
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

        association_id = self.data.get('association')
        if not association_id and Association.objects.exists():
            association_id = Association.objects.first().id

        if association_id:
            financial_years = Financial.objects.filter(association_id=association_id).values_list('tax_year', flat=True).distinct()
            self.fields['tax_year'].choices = [(str(year), str(year)) for year in financial_years]
            logger.debug(f"Tax years for association {association_id}: {self.fields['tax_year'].choices}")
        else:
            self.fields['tax_year'].choices = []
            logger.debug("No association selected, tax year choices empty")

class AssociationForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = ['association_name', 'mailing_address', 'city', 'state', 'zipcode', 'zoned', 'ein', 'formation_date', 'association_type']
        widgets = {
            'formation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'association_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'zoned':
                self.fields[field].widget.attrs['class'] = 'form-control'
        self.fields['zoned'].widget.attrs['class'] = 'form-check-input'

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