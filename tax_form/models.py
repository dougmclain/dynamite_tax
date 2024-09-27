

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
# Create your models here.
class Association(models.Model):
    ASSOCIATION_TYPES = (
        ('condo', 'Condominium'),
        ('homeowners', 'Homeowners'),
    )

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

    def __str__(self):
        return self.association_name



class Financial(models.Model):
    association = models.ForeignKey('Association', on_delete=models.CASCADE)
    tax_year = models.IntegerField(default=2023,help_text="The year this financial data pertains to")

    # ... (rest of your fields)

    name_change = models.BooleanField(default=False)
    address_change = models.BooleanField(default=False)
    prior_year_over_payment = models.PositiveIntegerField(default=0, blank=True, null=True)
    extension_payment = models.PositiveIntegerField(default=0, blank=True, null=True)
    estimated_payment = models.PositiveIntegerField(default=0, blank=True, null=True)


    #exempt income
    member_assessments = models.PositiveIntegerField(default=0)
    capital_contribution = models.PositiveIntegerField(default=0)
    moving_fees = models.PositiveIntegerField(default=0)
    utilities = models.PositiveIntegerField(default=0)
    late_fees = models.PositiveIntegerField(default=0)
    fines = models.PositiveIntegerField(default=0)
    other_exempt_income = models.PositiveBigIntegerField(default=0)

   #total expenses
    total_expenses = models.PositiveIntegerField(default=0)
    #non-exempt income
    interest = models.PositiveIntegerField(default=0)
    dividends = models.PositiveIntegerField(default=0)
    rentals = models.PositiveIntegerField(default=0)
    non_exempt_income_description1 =  models.CharField(max_length=100, blank=True)
    non_exempt_income_amount1 = models.PositiveIntegerField(default=0)
    non_exempt_income_description2 =  models.CharField(max_length=100, blank=True)
    non_exempt_income_amount2 = models.PositiveIntegerField(default=0)
    non_exempt_income_description3 =  models.CharField(max_length=100, blank=True)
    non_exempt_income_amount3 = models.PositiveIntegerField(default=0)

    #non-exempt expneses

    tax_preparation = models.PositiveIntegerField(default=0)
    management_fees = models.PositiveIntegerField(default=0)
    administration_fees = models.PositiveIntegerField(default=0)
    audit_fees = models.PositiveIntegerField(default=0)
    allocated_rental_expenses = models.PositiveIntegerField(default=0)

    non_exempt_expense_description1 =  models.CharField(max_length=100, blank=True)
    non_exempt_expense_amount1 = models.PositiveIntegerField(default=0)
    non_exempt_expense_description2 =  models.CharField(max_length=100, blank=True)
    non_exempt_expense_amount2 = models.PositiveIntegerField(default=0)
    non_exempt_expense_description3 =  models.CharField(max_length=100, blank=True)
    non_exempt_expense_amount3 = models.PositiveIntegerField(default=0)


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
