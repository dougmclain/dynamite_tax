

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator
from datetime import datetime, timedelta, date
import calendar
# Create your models here.



class ManagementCompany(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zipcode = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Management Company"
        verbose_name_plural = "Management Companies"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_full_address(self):
        """Return the full address as a formatted string"""
        if self.address and self.city and self.state and self.zipcode:
            return f"{self.address}, {self.city}, {self.state} {self.zipcode}"
        return "No address provided"

# Update the Association model by adding these fields:

# In the Association model, add these fields:
management_company = models.ForeignKey(
    'ManagementCompany', 
    on_delete=models.SET_NULL, 
    blank=True, 
    null=True, 
    related_name='associations'
)
is_self_managed = models.BooleanField(
    default=True, 
    help_text="Check if this association is self-managed (no management company)"
)

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

    # Filing state - where the association needs to file state returns (may differ from mailing address)
    STATE_CHOICES = (
        ('', 'Same as mailing address'),
        ('AL', 'Alabama'),
        ('AK', 'Alaska'),
        ('AZ', 'Arizona'),
        ('AR', 'Arkansas'),
        ('CA', 'California'),
        ('CO', 'Colorado'),
        ('CT', 'Connecticut'),
        ('DE', 'Delaware'),
        ('DC', 'District of Columbia'),
        ('FL', 'Florida'),
        ('GA', 'Georgia'),
        ('HI', 'Hawaii'),
        ('ID', 'Idaho'),
        ('IL', 'Illinois'),
        ('IN', 'Indiana'),
        ('IA', 'Iowa'),
        ('KS', 'Kansas'),
        ('KY', 'Kentucky'),
        ('LA', 'Louisiana'),
        ('ME', 'Maine'),
        ('MD', 'Maryland'),
        ('MA', 'Massachusetts'),
        ('MI', 'Michigan'),
        ('MN', 'Minnesota'),
        ('MS', 'Mississippi'),
        ('MO', 'Missouri'),
        ('MT', 'Montana'),
        ('NE', 'Nebraska'),
        ('NV', 'Nevada'),
        ('NH', 'New Hampshire'),
        ('NJ', 'New Jersey'),
        ('NM', 'New Mexico'),
        ('NY', 'New York'),
        ('NC', 'North Carolina'),
        ('ND', 'North Dakota'),
        ('OH', 'Ohio'),
        ('OK', 'Oklahoma'),
        ('OR', 'Oregon'),
        ('PA', 'Pennsylvania'),
        ('RI', 'Rhode Island'),
        ('SC', 'South Carolina'),
        ('SD', 'South Dakota'),
        ('TN', 'Tennessee'),
        ('TX', 'Texas'),
        ('UT', 'Utah'),
        ('VT', 'Vermont'),
        ('VA', 'Virginia'),
        ('WA', 'Washington'),
        ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'),
        ('WY', 'Wyoming'),
    )
    filing_state = models.CharField(
        max_length=2,
        choices=STATE_CHOICES,
        blank=True,
        default='',
        help_text="State where the association files state tax returns (if different from mailing address)"
    )

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
    
    # New fields for management company
    management_company = models.ForeignKey(
        'ManagementCompany', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='associations'
    )
    is_self_managed = models.BooleanField(
        default=True, 
        help_text="Check if this association is self-managed (no management company)"
    )

    def __str__(self):
        return self.association_name

    def get_full_contact_name(self):
        return f"{self.contact_first_name} {self.contact_last_name}"

    def get_filing_state(self):
        """Returns the state where this association needs to file state returns.
        Uses filing_state if set, otherwise falls back to the mailing address state."""
        if self.filing_state:
            return self.filing_state
        # Convert mailing address state to 2-letter code if needed
        state_map = {
            'Washington': 'WA', 'Oregon': 'OR', 'Illinois': 'IL',
            'California': 'CA', 'Texas': 'TX', 'Florida': 'FL',
            'Arizona': 'AZ', 'Nevada': 'NV', 'Colorado': 'CO',
        }
        return state_map.get(self.state, self.state[:2].upper() if len(self.state) >= 2 else self.state)

    def get_filing_state_display(self):
        """Returns the full name of the filing state."""
        state_code = self.get_filing_state()
        state_names = dict(self.STATE_CHOICES)
        return state_names.get(state_code, state_code)

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
    FILING_STATUS_CHOICES = (
        ('not_filed', 'Not Filed'),
        ('filed_by_dynamite', 'Filed by Dynamite'),
        ('filed_by_association', 'Filed by Association'),
    )
    
    financial = models.OneToOneField('Financial', on_delete=models.CASCADE, related_name='completed_tax_return')
    
    # Return filing status
    return_filed = models.BooleanField(default=False, help_text="Indicates whether the tax return has been filed")
    filing_status = models.CharField(max_length=20, choices=FILING_STATUS_CHOICES, default='not_filed', help_text="Who filed the tax return")
    date_prepared = models.DateField(null=True, blank=True, help_text="The date the tax return was prepared")
    
    # Return sent for signature
    sent_for_signature = models.BooleanField(default=False, help_text="Indicates whether the tax return was sent for signature")
    sent_date = models.DateField(null=True, blank=True, help_text="The date the tax return was sent for signature")
    sent_tax_return_pdf = models.FileField(upload_to='sent_tax_returns/', null=True, blank=True, help_text="PDF of the tax return sent for signature")
    
    # Signed return
    tax_return_pdf = models.FileField(upload_to='completed_tax_returns/', null=True, blank=True, help_text="PDF of the signed tax return")

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

class EngagementLetterTemplate(models.Model):
    """Base template for engagement letters per tax year"""
    tax_year = models.IntegerField(unique=True, help_text="Tax year this template applies to")

    # Customizable sections
    services_text = models.TextField(
        default="Dynamite Management, LLC will prepare the federal Form 1120H for the tax year ending December 31, {tax_year}. Our services will include the preparation of the tax forms based on the financial information provided by you. It is your responsibility to provide all the necessary information required for the preparation of complete and accurate returns.",
        help_text="Services section text. Use {tax_year} as placeholder."
    )
    fees_text = models.TextField(
        default="The fee for the preparation of the Form 1120H will be: ${price}. These fees are based on the assumption that all information provided by you is accurate and complete and that you will provide all required information in a timely manner. Any additional services or consultations beyond the scope of this engagement will be billed separately.",
        help_text="Fees section text. Use {price} as placeholder."
    )
    responsibilities_text = models.TextField(
        default="It is your responsibility to provide all the information required for the preparation of the tax returns. You are also responsible for reviewing the returns for accuracy and completeness before they are filed. You are responsible for the payment of all taxes due. You should retain all the documents and other data that form the basis of this return for at least seven (7) years.\n\nBy signing below, you are also taking responsibility for making all management decisions and performing all management functions; for designating an individual with suitable skill, knowledge, or experience to oversee the tax services provided.",
        help_text="Responsibilities section text."
    )
    consent_text = models.TextField(
        default="You acknowledge and agree that Dynamite Management, LLC may use your association's tax return information provided for the purpose of preparing your tax returns.",
        help_text="Consent section text."
    )
    default_price = models.PositiveIntegerField(default=150, help_text="Default price for new engagement letters")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Engagement Letter Template - {self.tax_year}"

    class Meta:
        ordering = ['-tax_year']


class StateEngagementTemplate(models.Model):
    """State-specific add-on content for engagement letters"""
    # All 50 US states + DC
    STATE_CHOICES = (
        ('AL', 'Alabama'),
        ('AK', 'Alaska'),
        ('AZ', 'Arizona'),
        ('AR', 'Arkansas'),
        ('CA', 'California'),
        ('CO', 'Colorado'),
        ('CT', 'Connecticut'),
        ('DE', 'Delaware'),
        ('DC', 'District of Columbia'),
        ('FL', 'Florida'),
        ('GA', 'Georgia'),
        ('HI', 'Hawaii'),
        ('ID', 'Idaho'),
        ('IL', 'Illinois'),
        ('IN', 'Indiana'),
        ('IA', 'Iowa'),
        ('KS', 'Kansas'),
        ('KY', 'Kentucky'),
        ('LA', 'Louisiana'),
        ('ME', 'Maine'),
        ('MD', 'Maryland'),
        ('MA', 'Massachusetts'),
        ('MI', 'Michigan'),
        ('MN', 'Minnesota'),
        ('MS', 'Mississippi'),
        ('MO', 'Missouri'),
        ('MT', 'Montana'),
        ('NE', 'Nebraska'),
        ('NV', 'Nevada'),
        ('NH', 'New Hampshire'),
        ('NJ', 'New Jersey'),
        ('NM', 'New Mexico'),
        ('NY', 'New York'),
        ('NC', 'North Carolina'),
        ('ND', 'North Dakota'),
        ('OH', 'Ohio'),
        ('OK', 'Oklahoma'),
        ('OR', 'Oregon'),
        ('PA', 'Pennsylvania'),
        ('RI', 'Rhode Island'),
        ('SC', 'South Carolina'),
        ('SD', 'South Dakota'),
        ('TN', 'Tennessee'),
        ('TX', 'Texas'),
        ('UT', 'Utah'),
        ('VT', 'Vermont'),
        ('VA', 'Virginia'),
        ('WA', 'Washington'),
        ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'),
        ('WY', 'Wyoming'),
    )

    state = models.CharField(max_length=2, choices=STATE_CHOICES, unique=True)
    is_active = models.BooleanField(default=True, help_text="Whether this state requires additional engagement letter content")

    # State form name (e.g., "Form IL-1120-ST", "Annual Report")
    state_form_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of the state form (e.g., 'Form IL-1120-ST', 'Annual Report')"
    )

    # State-specific services (e.g., state tax return preparation)
    state_services_text = models.TextField(
        blank=True,
        help_text="Additional services text for this state. Use {tax_year}, {state_name}, and {state_form_name} as placeholders."
    )

    # Default state filing fee
    default_state_fee = models.PositiveIntegerField(
        default=0,
        help_text="Default additional fee for state filing"
    )

    # State fee description (how to describe the fee)
    state_fee_text = models.TextField(
        blank=True,
        default="Additionally, there will be a fee of ${state_fee} for the preparation of the {state_name} state filing.",
        help_text="Text describing the state fee. Use {state_fee} and {state_name} as placeholders."
    )

    # State disclosure requirements
    state_disclosure_text = models.TextField(
        blank=True,
        help_text="State-specific disclosure or legal requirements text."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State Template - {self.get_state_display()}"

    def get_state_name(self):
        return dict(self.STATE_CHOICES).get(self.state, self.state)

    class Meta:
        ordering = ['state']


class EngagementLetter(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('signed', 'Signed'),
    )

    association = models.ForeignKey('Association', on_delete=models.CASCADE, related_name='engagement_letters')
    tax_year = models.IntegerField(default=datetime.now().year, help_text="Tax year this engagement is for")
    price = models.PositiveIntegerField(default=150, help_text="Price for federal tax preparation services")
    state_fee = models.PositiveIntegerField(default=0, help_text="Additional fee for state filing (0 if no state filing needed)")
    date_created = models.DateField(auto_now_add=True)
    date_signed = models.DateField(null=True, blank=True)
    signed_by = models.CharField(max_length=100, blank=True, null=True)
    signer_title = models.CharField(max_length=100, blank=True, null=True)
    pdf_file = models.FileField(upload_to='engagement_letters/', null=True, blank=True)
    signed_pdf = models.FileField(upload_to='signed_engagement_letters/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # Custom overrides (if blank, uses template defaults)
    custom_services_text = models.TextField(blank=True, null=True, help_text="Override services text for this letter only")
    custom_fees_text = models.TextField(blank=True, null=True, help_text="Override fees text for this letter only")
    custom_responsibilities_text = models.TextField(blank=True, null=True, help_text="Override responsibilities text for this letter only")
    custom_consent_text = models.TextField(blank=True, null=True, help_text="Override consent text for this letter only")

    def __str__(self):
        return f"{self.association.association_name} - {self.tax_year} Engagement Letter"

    def get_template(self):
        """Get the template for this letter's tax year, or None if not found"""
        return EngagementLetterTemplate.objects.filter(tax_year=self.tax_year).first()

    def get_state_template(self):
        """Get the state template for this letter's association filing state"""
        state = self.association.get_filing_state()
        if state:
            return StateEngagementTemplate.objects.filter(state=state, is_active=True).first()
        return None

    def get_services_text(self):
        if self.custom_services_text:
            return self.custom_services_text
        template = self.get_template()
        if template:
            return template.services_text.replace('{tax_year}', str(self.tax_year))
        return f"Dynamite Management, LLC will prepare the federal Form 1120H for the tax year ending December 31, {self.tax_year}."

    def get_state_services_text(self):
        """Get state-specific services text if applicable"""
        state_template = self.get_state_template()
        if state_template and state_template.state_services_text:
            text = state_template.state_services_text
            text = text.replace('{tax_year}', str(self.tax_year))
            text = text.replace('{state_name}', state_template.get_state_name())
            text = text.replace('{state_form_name}', state_template.state_form_name or '')
            return text
        return ""

    def get_fees_text(self):
        if self.custom_fees_text:
            return self.custom_fees_text.replace('{price}', str(self.price))
        template = self.get_template()
        if template:
            return template.fees_text.replace('{price}', str(self.price))
        return f"The fee for the preparation of the Form 1120H will be: ${self.price}"

    def get_state_fee_text(self):
        """Get state fee text if applicable"""
        if self.state_fee > 0:
            state_template = self.get_state_template()
            if state_template and state_template.state_fee_text:
                text = state_template.state_fee_text
                text = text.replace('{state_fee}', str(self.state_fee))
                text = text.replace('{state_name}', state_template.get_state_name())
                return text
            # Default text if no template
            state_name = dict(StateEngagementTemplate.STATE_CHOICES).get(self.association.state, self.association.state)
            return f"Additionally, there will be a fee of ${self.state_fee} for the preparation of the {state_name} state filing."
        return ""

    def get_total_fee(self):
        """Get total fee (federal + state)"""
        return self.price + self.state_fee

    def get_responsibilities_text(self):
        if self.custom_responsibilities_text:
            return self.custom_responsibilities_text
        template = self.get_template()
        return template.responsibilities_text if template else ""

    def get_consent_text(self):
        if self.custom_consent_text:
            return self.custom_consent_text
        template = self.get_template()
        return template.consent_text if template else ""

    def get_state_disclosure_text(self):
        """Get state-specific disclosure text if applicable"""
        state_template = self.get_state_template()
        if state_template and state_template.state_disclosure_text:
            return state_template.state_disclosure_text
        return ""

    class Meta:
        unique_together = ('association', 'tax_year')
        
# Add to tax_form/models.py

# Add to tax_form/models.py

class AssociationFilingStatus(models.Model):
    """Tracks filing status and invoicing per association and tax year"""
    association = models.ForeignKey('Association', on_delete=models.CASCADE, related_name='filing_statuses')
    tax_year = models.IntegerField(help_text="The tax year this status applies to")
    
    # Whether we'll be preparing/filing taxes for this association this year
    prepare_return = models.BooleanField(default=True, 
                      help_text="If False, we won't be preparing a tax return for this association this year")
    
    # Reason for not preparing, if applicable
    not_filing_reason = models.CharField(max_length=255, blank=True, 
                        help_text="Reason for not preparing a tax return")
    
    # Invoice tracking - simplified
    invoiced = models.BooleanField(default=False, help_text="Has this association been invoiced?")
    
    class Meta:
        unique_together = ('association', 'tax_year')
        verbose_name_plural = "Association Filing Statuses"
    
    def __str__(self):
        status = "Will prepare" if self.prepare_return else "Will NOT prepare"
        invoice_status = "Invoiced" if self.invoiced else "Not invoiced"
        return f"{self.association.association_name} - {self.tax_year}: {status}, {invoice_status}"
    
    
# Update tax_form/models.py to add the ManagementCompany model
# and update the Association model

# Add this new model class
