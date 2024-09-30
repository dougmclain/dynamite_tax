def calculate_total_exempt_income(financial):
    """Calculate total exempt income."""
    return int(
        financial.member_assessments +
        financial.moving_fees +
        financial.utilities +
        financial.late_fees +
        financial.fines +
        financial.other_exempt_income -
        financial.capital_contribution
    )

def calculate_expenses_lineC(financial):
    """Calculate expenses for Line C (90% test)."""
    return int(financial.total_expenses -
            (calculate_rental_expenses(financial) +
             calculate_other_nonexempt_expense1(financial) +
             calculate_other_nonexempt_expense2(financial) +
             calculate_other_nonexempt_expense3(financial)))

def calculate_total_expenses(financial):
    """Calculate total expenses."""
    return int(financial.total_expenses)

def calculate_interest_income(financial):
    """Calculate interest income."""
    return int(financial.interest)

def calculate_dividend_income(financial):
    """Calculate dividend income."""
    return int(financial.dividends)

def calculate_rental_income(financial):
    """Calculate rental income."""
    return int(financial.rentals)

def calculate_total_other_income(financial):
    """Calculate total other income."""
    return int(
        financial.non_exempt_income_amount1 +
        financial.non_exempt_income_amount2 +
        financial.non_exempt_income_amount3
    )

def calculate_gross_income(financial):
    """Calculate gross income."""
    total_other_income = calculate_total_other_income(financial)
    return int(total_other_income + financial.rentals + financial.dividends + financial.interest)

def calculate_tax_prep_expenses(financial):
    """Calculate tax preparation expenses."""
    bank_interest_dividends = financial.interest + financial.dividends
    total_non_exempt_income = bank_interest_dividends + financial.rentals + financial.non_exempt_income_amount1 + financial.non_exempt_income_amount2 + financial.non_exempt_income_amount3

    if total_non_exempt_income <= 100 or bank_interest_dividends <= 100:
        return 0
    elif bank_interest_dividends > 100 and financial.tax_preparation >= bank_interest_dividends:
        return int(bank_interest_dividends)
    else:
        return int(financial.tax_preparation)

def calculate_management_fees(financial, tax_prep_expenses):
    """Calculate management fees."""
    bank_interest_dividends = financial.interest + financial.dividends
    total_non_exempt_income = (
        bank_interest_dividends +
        financial.rentals +
        financial.non_exempt_income_amount1 +
        financial.non_exempt_income_amount2 +
        financial.non_exempt_income_amount3
    )
    total_exempt_income = calculate_total_exempt_income(financial)
    total_revenue = total_exempt_income + total_non_exempt_income

    if total_revenue == 0:
        return 0

    interest_income_ratio = bank_interest_dividends / total_revenue
    limit_ratio = max(interest_income_ratio, 0.05)
    limited_management_fees = limit_ratio * financial.management_fees

    if total_non_exempt_income - tax_prep_expenses <= 100 or bank_interest_dividends <= 100:
        return 0
    elif 0 < bank_interest_dividends - tax_prep_expenses <= limited_management_fees:
        return int(bank_interest_dividends - tax_prep_expenses)
    else:
        return int(limited_management_fees)

def calculate_audit_fees(financial, tax_prep_expenses, management_fees):
    """Calculate audit fees."""
    bank_interest_dividends = financial.interest + financial.dividends
    total_non_exempt_income = (
        bank_interest_dividends +
        financial.rentals +
        financial.non_exempt_income_amount1 +
        financial.non_exempt_income_amount2 +
        financial.non_exempt_income_amount3
    )

    if total_non_exempt_income - tax_prep_expenses - management_fees <= 100:
        return 0
    elif bank_interest_dividends - tax_prep_expenses - management_fees == 0:
        return 0
    elif 0 < bank_interest_dividends - tax_prep_expenses - management_fees <= financial.audit_fees:
        return int(bank_interest_dividends - tax_prep_expenses - management_fees)
    else:
        return int(financial.audit_fees) if bank_interest_dividends - tax_prep_expenses - management_fees > 0 else 0

def calculate_rental_expenses(financial):
    """Calculate rental expenses."""
    bank_interest_dividends = financial.interest + financial.dividends
    rental_income = financial.rentals

    if rental_income == 0:
        return 0
    elif rental_income + bank_interest_dividends <= 100:
        return 0
    elif 0 < rental_income <= financial.allocated_rental_expenses:
        return int(rental_income)
    else:
        return int(financial.allocated_rental_expenses)

def calculate_other_nonexempt_expense1(financial):
    """Calculate other non-exempt expense 1."""
    bank_interest_dividends = financial.interest + financial.dividends
    rental_income = financial.rentals
    non_exempt_income1 = financial.non_exempt_income_amount1

    if non_exempt_income1 == 0:
        return 0
    elif non_exempt_income1 + bank_interest_dividends + rental_income <= 100:
        return 0
    elif 0 < non_exempt_income1 <= financial.non_exempt_expense_amount1:
        return int(non_exempt_income1)
    else:
        return int(financial.non_exempt_expense_amount1)

def calculate_other_nonexempt_expense2(financial):
    """Calculate other non-exempt expense 2."""
    bank_interest_dividends = financial.interest + financial.dividends
    rental_income = financial.rentals
    non_exempt_income1 = financial.non_exempt_income_amount1
    non_exempt_income2 = financial.non_exempt_income_amount2

    if non_exempt_income2 == 0:
        return 0
    elif non_exempt_income2 + bank_interest_dividends + rental_income + non_exempt_income1 <= 100:
        return 0
    elif 0 < non_exempt_income2 <= financial.non_exempt_expense_amount2:
        return int(non_exempt_income2)
    else:
        return int(financial.non_exempt_expense_amount2)

def calculate_other_nonexempt_expense3(financial):
    """Calculate other non-exempt expense 3."""
    bank_interest_dividends = financial.interest + financial.dividends
    rental_income = financial.rentals
    non_exempt_income1 = financial.non_exempt_income_amount1
    non_exempt_income2 = financial.non_exempt_income_amount2
    non_exempt_income3 = financial.non_exempt_income_amount3

    if non_exempt_income3 == 0:
        return 0
    elif non_exempt_income3 + bank_interest_dividends + rental_income + non_exempt_income1 + non_exempt_income2 <= 100:
        return 0
    elif 0 < non_exempt_income3 <= financial.non_exempt_expense_amount3:
        return int(non_exempt_income3)
    else:
        return int(financial.non_exempt_expense_amount3)

def calculate_other_deductions(financial):
    """Calculate other deductions."""
    tax_prep_expenses = calculate_tax_prep_expenses(financial)
    management_fees = calculate_management_fees(financial, tax_prep_expenses)
    return int(
        tax_prep_expenses +
        management_fees +
        calculate_audit_fees(financial, tax_prep_expenses, management_fees) +
        calculate_rental_expenses(financial) +
        calculate_other_nonexempt_expense1(financial) +
        calculate_other_nonexempt_expense2(financial) +
        calculate_other_nonexempt_expense3(financial)
    )

def calculate_total_deductions(financial):
    """Calculate total deductions."""
    return int(calculate_other_deductions(financial))

def calculate_taxable_income_before_100(financial):
    """Calculate taxable income before $100 deduction."""
    gross_income = calculate_gross_income(financial)
    total_deductions = calculate_total_deductions(financial)
    return int(gross_income - total_deductions)

def calculate_taxable_income(financial):
    """Calculate taxable income."""
    taxable_income_before_100 = calculate_taxable_income_before_100(financial)
    return int(max(0, taxable_income_before_100 - 100))

def calculate_total_tax(financial):
    """Calculate total tax."""
    return int(round(calculate_taxable_income(financial) * 0.30))

def calculate_total_payments(financial):
    """Calculate total payments."""
    return int(financial.prior_year_over_payment + financial.extension_payment + financial.estimated_payment)

def calculate_amount_owed(total_tax, total_payments):
    """Calculate amount owed."""
    return int(max(0, total_tax - total_payments))

def calculate_overpayment(total_tax, total_payments):
    """Calculate overpayment."""
    return int(max(0, total_payments - total_tax))

def calculate_refunded_amount(overpayment):
    """Calculate refunded amount."""
    return int(overpayment)

def calculate_financial_info(financial, association):
    """Calculate all financial information needed for the form."""
    return {
        'tax_year': financial.tax_year,
        'total_exempt_income': calculate_total_exempt_income(financial),
        'expenses_lineC': calculate_expenses_lineC(financial),
        'total_expenses': calculate_total_expenses(financial),
        'interest_income': calculate_interest_income(financial),
        'dividend_income': calculate_dividend_income(financial),
        'rental_income': calculate_rental_income(financial),
        'total_other_income': calculate_total_other_income(financial),
        'total_taxable_income': calculate_taxable_income(financial),
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