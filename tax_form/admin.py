from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.contrib.humanize.templatetags.humanize import intcomma
from .models import Association, Financial, Preparer

@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ('association_name', 'city', 'state', 'ein', 'association_type')
    search_fields = ('association_name', 'ein')
    list_filter = ('association_type', 'state')

@admin.register(Financial)
class FinancialAdmin(admin.ModelAdmin):
    def format_currency(self, value):
        return f"${intcomma(value)}"

    list_display = ('association', 'tax_year', 'member_assessments_display', 'total_expenses_display')
    list_filter = ('tax_year',)
    search_fields = ('association__association_name',)
    
    readonly_fields = (
        'member_assessments_display', 'capital_contribution_display', 'moving_fees_display',
        'utilities_display', 'late_fees_display', 'fines_display', 'other_exempt_income_display',
        'total_expenses_display', 'interest_display', 'dividends_display', 'rentals_display',
        'non_exempt_income_amount1_display', 'non_exempt_income_amount2_display', 'non_exempt_income_amount3_display',
        'tax_preparation_display', 'management_fees_display', 'administration_fees_display',
        'audit_fees_display', 'allocated_rental_expenses_display',
        'non_exempt_expense_amount1_display', 'non_exempt_expense_amount2_display', 'non_exempt_expense_amount3_display'
    )

    fieldsets = (
        ('Association Information', {
            'fields': ('association', 'tax_year')
        }),
        ('Exempt Income', {
            'fields': (
                'member_assessments_display', 'capital_contribution_display', 'moving_fees_display',
                'utilities_display', 'late_fees_display', 'fines_display', 'other_exempt_income_display'
            )
        }),
        ('Non-Exempt Income', {
            'fields': (
                'interest_display', 'dividends_display', 'rentals_display',
                'non_exempt_income_description1', 'non_exempt_income_amount1_display',
                'non_exempt_income_description2', 'non_exempt_income_amount2_display',
                'non_exempt_income_description3', 'non_exempt_income_amount3_display'
            )
        }),
        ('Expenses', {
            'fields': (
                'total_expenses_display', 'tax_preparation_display', 'management_fees_display',
                'administration_fees_display', 'audit_fees_display', 'allocated_rental_expenses_display',
                'non_exempt_expense_description1', 'non_exempt_expense_amount1_display',
                'non_exempt_expense_description2', 'non_exempt_expense_amount2_display',
                'non_exempt_expense_description3', 'non_exempt_expense_amount3_display'
            )
        })
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('association', 'tax_year')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        for field in self.model._meta.fields:
            if not field.name.endswith('_display'):
                setattr(obj, field.name, form.cleaned_data.get(field.name, getattr(obj, field.name)))
        super().save_model(request, obj, form, change)

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        for field in model._meta.fields:
            if isinstance(field, (models.IntegerField, models.PositiveIntegerField)):
                method_name = f'{field.name}_display'
                setattr(self, method_name, lambda obj, f=field: self.format_currency(getattr(obj, f.name)))
                getattr(self, method_name).short_description = field.verbose_name.title()

@admin.register(Preparer)
class PreparerAdmin(admin.ModelAdmin):
    list_display = ('name', 'ptin', 'firm_name', 'user')
    search_fields = ('name', 'firm_name', 'ptin')
    list_filter = ('firm_name',)

admin.site.site_header = "Dynamite Tax Services"
admin.site.site_title = "Dynamite Tax Services"
admin.site.index_title = "Dynamite Tax Services Admin Portal"