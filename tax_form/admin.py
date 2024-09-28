from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.contrib.humanize.templatetags.humanize import intcomma
from .models import Association, Financial, Preparer

# Inline for Financial records in Association admin (optional)
class FinancialInline(admin.TabularInline):
    model = Financial
    extra = 0
    fields = ('tax_year', 'total_expenses_display')
    readonly_fields = ('total_expenses_display',)

    def total_expenses_display(self, obj):
        return f"${intcomma(obj.total_expenses)}"
    total_expenses_display.short_description = 'Total Expenses'

@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ('association_name', 'city', 'state', 'ein', 'association_type')
    search_fields = ('association_name', 'ein')
    list_filter = ('association_type', 'state')
    inlines = [FinancialInline]  # Include this if you want Financials inline

@admin.register(Financial)
class FinancialAdmin(admin.ModelAdmin):
    list_display = ('association', 'tax_year', 'member_assessments_display', 'total_expenses_display')
    list_filter = ('tax_year', 'association__association_name')
    search_fields = ('association__association_name', 'tax_year')
    def format_currency(self, value):
        return f"${intcomma(value)}"

    # Read-only display fields
    readonly_fields = (
        'member_assessments_display', 'capital_contribution_display', 'moving_fees_display',
        'utilities_display', 'late_fees_display', 'fines_display', 'other_exempt_income_display',
        'total_expenses_display', 'interest_display', 'dividends_display', 'rentals_display',
        'non_exempt_income_amount1_display', 'non_exempt_income_amount2_display', 'non_exempt_income_amount3_display',
        'tax_preparation_display', 'management_fees_display', 'administration_fees_display',
        'audit_fees_display', 'allocated_rental_expenses_display',
        'non_exempt_expense_amount1_display', 'non_exempt_expense_amount2_display', 'non_exempt_expense_amount3_display'
    )

    # Include both actual fields and their display counterparts
    fieldsets = (
        ('Association Information', {
            'fields': ('association', 'tax_year')
        }),
        ('Exempt Income', {
            'fields': (
                ('member_assessments', 'member_assessments_display'),
                ('capital_contribution', 'capital_contribution_display'),
                ('moving_fees', 'moving_fees_display'),
                ('utilities', 'utilities_display'),
                ('late_fees', 'late_fees_display'),
                ('fines', 'fines_display'),
                ('other_exempt_income', 'other_exempt_income_display'),
            )
        }),
        ('Non-Exempt Income', {
            'fields': (
                ('interest', 'interest_display'),
                ('dividends', 'dividends_display'),
                ('rentals', 'rentals_display'),
                'non_exempt_income_description1',
                ('non_exempt_income_amount1', 'non_exempt_income_amount1_display'),
                'non_exempt_income_description2',
                ('non_exempt_income_amount2', 'non_exempt_income_amount2_display'),
                'non_exempt_income_description3',
                ('non_exempt_income_amount3', 'non_exempt_income_amount3_display'),
            )
        }),
        ('Expenses', {
            'fields': (
                ('total_expenses', 'total_expenses_display'),
                ('tax_preparation', 'tax_preparation_display'),
                ('management_fees', 'management_fees_display'),
                ('administration_fees', 'administration_fees_display'),
                ('audit_fees', 'audit_fees_display'),
                ('allocated_rental_expenses', 'allocated_rental_expenses_display'),
                'non_exempt_expense_description1',
                ('non_exempt_expense_amount1', 'non_exempt_expense_amount1_display'),
                'non_exempt_expense_description2',
                ('non_exempt_expense_amount2', 'non_exempt_expense_amount2_display'),
                'non_exempt_expense_description3',
                ('non_exempt_expense_amount3', 'non_exempt_expense_amount3_display'),
            )
        })
    )

    # Only display fields are read-only
    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields

    # Dynamically create display methods for currency formatting
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        for field in model._meta.fields:
            if isinstance(field, (models.IntegerField, models.PositiveIntegerField, models.PositiveBigIntegerField)):
                method_name = f'{field.name}_display'
                setattr(self, method_name, self.make_display_method(field.name))
                getattr(self, method_name).short_description = field.verbose_name.replace('_', ' ').title()

    def make_display_method(self, field_name):
        def _method(obj):
            value = getattr(obj, field_name)
            return self.format_currency(value)
        return _method

    # Optional: Remove custom save_model if unnecessary
    # def save_model(self, request, obj, form, change):
    #     super().save_model(request, obj, form, change)

@admin.register(Preparer)
class PreparerAdmin(admin.ModelAdmin):
    list_display = ('name', 'ptin', 'firm_name', 'user')
    search_fields = ('name', 'firm_name', 'ptin')
    list_filter = ('firm_name',)

# Customize the admin site headers
admin.site.site_header = "Dynamite Tax Services"
admin.site.site_title = "Dynamite Tax Services"
admin.site.index_title = "Dynamite Tax Services Admin Portal"
