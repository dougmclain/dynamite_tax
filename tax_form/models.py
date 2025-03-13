

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator
from datetime import datetime, timedelta, date
import calendar
# Create your models here.
class Association(models.Model):
    ASSOCIATION_TYPES = (
        ('condo', 'Condominium'),
        ('homeowners', 'Homeowners'),
    )

    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    association_name = models.CharField(max_length=255)
    mailing_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=20)
    zoned = models.BooleanField(default=True)
    ein = models.CharField(max_length=11, unique=True, validators=[
        RegexValidator(
            regex=r'^\d{2}-\d{7}$',
            message="EIN must be in the format 'XX-XXXXXXX'."
        )
    ])
    formation_date = models.DateField()
    association_type = models.CharField(max_length=10, choices=ASSOCIATION_TYPES)
    fiscal_year_end_month = models.IntegerField(choices=MONTH_CHOICES, default=12)
    
    contact_first_name = models.CharField(max_length=100, null=True, blank=True)
    contact_last_name = models.CharField(max_length=100, null=True, blank=True)
    contact_email = models.EmailField(max_length=254, null=True, blank=True)

    def __str__(self):
        return self.association_name

    def get_full_contact_name(self):
        return f"{self.contact_first_name} {self.contact_last_name}"

    def get_fiscal_year_end(self, tax_year):
        _, last_day = calendar.monthrange(tax_year, self.fiscal_year_end_month)
        return date(tax_year, self.fiscal_year_end_month, last_day)

    def adjust_for_weekend(self, check_date):
        while check_date.weekday() >= 5:  # Saturday or Sunday
            check_date += timedelta(days=1)
        return check_date

    def get_tax_return_due_date(self, tax_year):
        fiscal_year_end = self.get_fiscal_year_end(tax_year)
        due_date = fiscal_year_end + timedelta(days=106)  # 3.5 months (approximately 106 days)
        
        # Adjust for leap years if necessary
        if calendar.isleap(due_date.year) and due_date >= date(due_date.year, 3, 1):
            due_date += timedelta(days=1)
        
        # Adjust for weekends
        due_date = self.adjust_for_weekend(due_date)
        
        return due_date

    def get_extended_due_date(self, tax_year):
        original_due_date = self.get_tax_return_due_date(tax_year)
        
        # Calculate the target month and day for the extended due date
        target_month = 10  # October
        target_day = 15
        
        # Create the extended due date
        extended_due_date = date(original_due_date.year, target_month, target_day)
        
        # If the original due date is after April 15 due to weekends,
        # but October 15 is a weekday, we keep October 15
        if original_due_date.month == 4 and original_due_date.day > 15:
            if extended_due_date.weekday() < 5:  # If Oct 15 is a weekday
                return extended_due_date
        
        # Otherwise, adjust for weekends
        return self.adjust_for_weekend(extended_due_date)

class Financial(models.Model):
    association = models.ForeignKey('Association', on_delete=models.CASCADE)
    tax_year = models.IntegerField(default=2023, help_text="The year this financial data pertains to")
    financial_info_pdf = models.FileField(upload_to='financial_info/', null=True, blank=True)
    
    # Engagement letter fields
    engagement_letter = models.FileField(upload_to='engagement_letters/', null=True, blank=True)
    engagement_letter_date = models.DateField(null=True, blank=True)

    # Existing fields
    name_change = models.BooleanField(default=False)
    address_change = models.BooleanField(default=False)
    prior_year_over_payment = models.PositiveIntegerField(default=0, blank=True, null=True)
    extension_payment = models.PositiveIntegerField(default=0, blank=True, null=True)
    estimated_payment = models.PositiveIntegerField(default=0, blank=True, null=True)

    # Exempt income
    member_assessments = models.PositiveIntegerField(default=0)
    capital_contribution = models.PositiveIntegerField(default=0)
    moving_fees = models.PositiveIntegerField(default=0)
    utilities = models.PositiveIntegerField(default=0)
    late_fees = models.PositiveIntegerField(default=0)
    fines = models.PositiveIntegerField(default=0)
    other_exempt_income = models.PositiveBigIntegerField(default=0)

    # Total expenses
    total_expenses = models.PositiveIntegerField(default=0)
    
    # Non-exempt income
    interest = models.PositiveIntegerField(default=0)
    dividends = models.PositiveIntegerField(default=0)
    rentals = models.PositiveIntegerField(default=0)
    non_exempt_income_description1 = models.CharField(max_length=100, blank=True)
    non_exempt_income_amount1 = models.PositiveIntegerField(default=0)
    non_exempt_income_description2 = models.CharField(max_length=100, blank=True)
    non_exempt_income_amount2 = models.PositiveIntegerField(default=0)
    non_exempt_income_description3 = models.CharField(max_length=100, blank=True)
    non_exempt_income_amount3 = models.PositiveIntegerField(default=0)

    # Non-exempt expenses
    tax_preparation = models.PositiveIntegerField(default=0)
    management_fees = models.PositiveIntegerField(default=0)
    administration_fees = models.PositiveIntegerField(default=0)
    audit_fees = models.PositiveIntegerField(default=0)
    allocated_rental_expenses = models.PositiveIntegerField(default=0)

    non_exempt_expense_description1 = models.CharField(max_length=100, blank=True)
    non_exempt_expense_amount1 = models.PositiveIntegerField(default=0)
    non_exempt_expense_description2 = models.CharField(max_length=100, blank=True)
    non_exempt_expense_amount2 = models.PositiveIntegerField(default=0)
    non_exempt_expense_description3 = models.CharField(max_length=100, blank=True)
    non_exempt_expense_amount3 = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('association', 'tax_year')

    def __str__(self):
        return f"{self.association.association_name} - {self.tax_year} Financial Data"
    
class Extension(models.Model):
    financial = models.OneToOneField('Financial', on_delete=models.CASCADE, related_name='extension')
    filed = models.BooleanField(default=False, help_text="Indicates whether the extension has been filed")
    filed_date = models.DateField(null=True, blank=True, help_text="The date the extension was filed")
    form_7004 = models.FileField(upload_to='extensions/', null=True, blank=True)
    
    # New fields for Form 7004
    tentative_tax = models.PositiveIntegerField(default=0, help_text="Form 7004 Line 6 - Tentative total tax")
    total_payments = models.PositiveIntegerField(default=0, help_text="Form 7004 Line 7 - Total payments and credits")
    balance_due = models.PositiveIntegerField(default=0, help_text="Form 7004 Line 8 - Balance due")

    def __str__(self):
        status = "Filed" if self.filed else "Not Filed"
        date_info = f" on {self.filed_date}" if self.filed_date else ""
        return f"{self.financial.association.association_name} - {self.financial.tax_year} Extension ({status}{date_info})"

    @property
    def tax_year(self):
        return self.financial.tax_year

    @property
    def association(self):
        return self.financial.association

    def calculate_balance_due(self):
        """Calculate balance due as max(0, tentative_tax - total_payments)"""
        return max(0, self.tentative_tax - self.total_payments)

    def save(self, *args, **kwargs):
        self.balance_due = self.calculate_balance_due()
        super().save(*args, **kwargs)
    
class CompletedTaxReturn(models.Model):
    financial = models.OneToOneField('Financial', on_delete=models.CASCADE, related_name='completed_tax_return')
    return_filed = models.BooleanField(default=False, help_text="Indicates whether the tax return has been filed")
    date_prepared = models.DateField(null=True, blank=True, help_text="The date the tax return was prepared")
    tax_return_pdf = models.FileField(upload_to='completed_tax_returns/', null=True, blank=True)

    def __str__(self):
        status = "Filed" if self.return_filed else "Not Filed"
        date_info = f" on {self.date_prepared}" if self.date_prepared else ""
        return f"{self.financial.association.association_name} - {self.financial.tax_year} Tax Return ({status}{date_info})"

    @property
    def tax_year(self):
        return self.financial.tax_year

    @property
    def association(self):
        return self.financial.association

class Preparer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    signature = models.CharField(max_length=255)
    ptin = models.CharField(max_length=20)
    sign_date = models.DateField(null=True, blank=True)
    firm_name = models.CharField(max_length=255)
    firm_ein = models.CharField(max_length=20)
    firm_address = models.CharField(max_length=255)
    firm_phone = models.CharField(max_length=20)

    def get_signature(self):
        return self.signature if self.signature else self.name

    def __str__(self):
        return self.name

class EngagementLetter(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('signed', 'Signed'),
    )
    
    association = models.ForeignKey('Association', on_delete=models.CASCADE, related_name='engagement_letters')
    tax_year = models.IntegerField(default=datetime.now().year, help_text="Tax year this engagement is for")
    price = models.PositiveIntegerField(default=150, help_text="Price for tax preparation services")
    date_created = models.DateField(auto_now_add=True)
    date_signed = models.DateField(null=True, blank=True)
    signed_by = models.CharField(max_length=100, blank=True, null=True)
    signer_title = models.CharField(max_length=100, blank=True, null=True)
    pdf_file = models.FileField(upload_to='engagement_letters/', null=True, blank=True)
    signed_pdf = models.FileField(upload_to='signed_engagement_letters/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.association.association_name} - {self.tax_year} Engagement Letter"
    
    class Meta:
        unique_together = ('association', 'tax_year')