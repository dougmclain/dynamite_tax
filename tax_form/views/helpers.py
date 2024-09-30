import logging
from datetime import date
from ..tax_calculations import *
from ..models import Extension

logger = logging.getLogger(__name__)

def calculate_financial_info(financial, association):
    """Calculate all financial information needed for the form."""
    info = {
        'tax_year': financial.tax_year,
        'total_exempt_income': calculate_total_exempt_income(financial),
        'expenses_lineC': calculate_expenses_lineC(financial),
        'total_expenses': calculate_total_expenses(financial),
        'interest_income': calculate_interest_income(financial),
        'dividend_income': calculate_dividend_income(financial),
        'rental_income': calculate_rental_income(financial),
        'total_other_income': calculate_total_other_income(financial),
        'gross_income': calculate_gross_income(financial),
        'other_deductions': calculate_other_deductions(financial),
        'total_deductions': calculate_total_deductions(financial),
        'taxable_income_before_100': calculate_taxable_income_before_100(financial),
        'taxable_income': calculate_taxable_income(financial),
        'total_tax': calculate_total_tax(financial),
        'total_payments': calculate_total_payments(financial),
        'amount_owed': calculate_amount_owed(calculate_total_tax(financial), calculate_total_payments(financial)),
        'overpayment': calculate_overpayment(calculate_total_tax(financial), calculate_total_payments(financial)),
        'refunded': calculate_refunded_amount(calculate_overpayment(calculate_total_tax(financial), calculate_total_payments(financial))),
        'estimated_payments': financial.estimated_payment,
        'extension_payment': financial.extension_payment,
        'name_change': bool(financial.name_change),
        'address_change': bool(financial.address_change),
        'condo': association.association_type == 'condo',
        'homeowners': association.association_type == 'homeowners',
    }

    # Add extension information if it exists
    try:
        extension = financial.extension
        if extension.filed and extension.form_7004:
            info['extension_info'] = {
                'tax_year': extension.tax_year,
                'filed_date': extension.filed_date,
                'form_7004_url': extension.form_7004.name,
            }
    except Extension.DoesNotExist:
        pass  # No extension exists for this financial record

    # Add detailed breakdown of other deductions
    tax_prep_expenses = calculate_tax_prep_expenses(financial)
    management_fees = calculate_management_fees(financial, tax_prep_expenses)
    audit_fees = calculate_audit_fees(financial, tax_prep_expenses, management_fees)
    rental_expenses = calculate_rental_expenses(financial)
    other_nonexempt_expense1 = calculate_other_nonexempt_expense1(financial)
    other_nonexempt_expense2 = calculate_other_nonexempt_expense2(financial)
    other_nonexempt_expense3 = calculate_other_nonexempt_expense3(financial)

    info['other_deductions_detail'] = [
        {'description': 'Tax Preparation Expenses', 'amount': tax_prep_expenses},
        {'description': 'Management Fees', 'amount': management_fees},
        {'description': 'Audit Fees', 'amount': audit_fees},
        {'description': 'Rental Expenses', 'amount': rental_expenses},
        {'description': financial.non_exempt_expense_description1 or 'Other Non-Exempt Expense 1', 'amount': other_nonexempt_expense1},
        {'description': financial.non_exempt_expense_description2 or 'Other Non-Exempt Expense 2', 'amount': other_nonexempt_expense2},
        {'description': financial.non_exempt_expense_description3 or 'Other Non-Exempt Expense 3', 'amount': other_nonexempt_expense3},
    ]

    return info

def format_number(value):
    """Format a number with commas for thousands separators."""
    if value is None or value == '':
        return ''
    try:
        return f"{int(float(value)):,}"
    except ValueError:
        logger.warning(f"Unable to format number: {value}")
        return str(value)

def get_statement_details(financial):
    """Get additional income and expense details for the statement."""
    statement_details = {
        'additional_income': [],
        'additional_expenses': []
    }
    if financial is None:
        return statement_details

    # Include additional income details
    for i in range(1, 4):
        income_amount = getattr(financial, f'non_exempt_income_amount{i}')
        if income_amount > 0:
            description = getattr(financial, f'non_exempt_income_description{i}', f'Other Non-Exempt Income {i}')
            statement_details['additional_income'].append({
                'description': description,
                'amount': income_amount
            })

    # Include additional expenses details
    rental_expenses = calculate_rental_expenses(financial)
    if rental_expenses > 0:
        statement_details['additional_expenses'].append({
            'description': 'Allocated Rental Expenses',
            'amount': rental_expenses
        })

    tax_prep_expenses = calculate_tax_prep_expenses(financial)
    if tax_prep_expenses > 0:
        statement_details['additional_expenses'].append({
            'description': 'Tax Preparation Expenses',
            'amount': tax_prep_expenses
        })

    management_fees = calculate_management_fees(financial, tax_prep_expenses)
    if management_fees > 0:
        statement_details['additional_expenses'].append({
            'description': 'Management Fees',
            'amount': management_fees
        })

    audit_fees = calculate_audit_fees(financial, tax_prep_expenses, management_fees)
    if audit_fees > 0:
        statement_details['additional_expenses'].append({
            'description': 'Audit Fees',
            'amount': audit_fees
        })

    for i in range(1, 4):
        expense_amount = getattr(financial, f'non_exempt_expense_amount{i}')
        if expense_amount > 0:
            description = getattr(financial, f'non_exempt_expense_description{i}', f'Other Non-Exempt Expense {i}')
            statement_details['additional_expenses'].append({
                'description': description,
                'amount': expense_amount
            })

    return statement_details

def prepare_pdf_data(financial_info, association, preparer):
    """Prepare data for PDF generation."""
    return {
        "f1_1": association.association_name,
        "f1_2": association.ein,
        "f1_3": association.mailing_address,
        "f1_4": f"{association.city}, {association.state} {association.zipcode}",
        "f1_5": association.formation_date.strftime("%m/%d/%Y"),
        
        # Checkboxes as booleans
        "name_change": financial_info.get('name_change', False),
        "address_change": financial_info.get('address_change', False),
        "condo": financial_info.get('condo', False),
        "homeowners": financial_info.get('homeowners', False),
        
        # Use raw numbers instead of formatted strings
        "f1_6": financial_info.get('total_exempt_income'),
        "f1_7": financial_info.get('expenses_lineC'),
        "f1_8": financial_info.get('total_expenses'),
        "f1_9": financial_info.get('dividend_income'),
        "f1_10": financial_info.get('interest_income'),
        "f1_11": financial_info.get('rental_income'),
        "f1_15": financial_info.get('total_other_income'),
        "f1_16": financial_info.get('gross_income'),
        "f1_23": financial_info.get('other_deductions'),
        "f1_24": financial_info.get('total_deductions'),
        "f1_25": financial_info.get('taxable_income_before_100'),
        "f1_27": financial_info.get('taxable_income'),
        "f1_28": financial_info.get('total_tax'),
        "f1_30": financial_info.get('total_tax'),
        "f1_31": financial_info.get('estimated_payments'),
        "f1_32": financial_info.get('extension_payment'),
        "f1_35": financial_info.get('total_payments'),
        "f1_36": financial_info.get('amount_owed'),
        "f1_37": financial_info.get('overpayment'),
        "f1_38": financial_info.get('refunded'),
        
        # Preparer information
        "f1_39": preparer.name if preparer else '',
        "f1_40": preparer.ptin if preparer else '',
        "f1_41": preparer.firm_name if preparer else '',
        "f1_42": preparer.firm_ein if preparer else '',
        "f1_43": preparer.firm_address if preparer else '',
        "f1_44": preparer.firm_phone if preparer else '',
        "f1_45": date.today().strftime("%m/%d/%Y"),  # Preparer sign date
        "f1_46": preparer.signature if preparer else '',  # Preparer signature
    }