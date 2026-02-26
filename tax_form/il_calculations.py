"""Illinois IL-1120 tax calculations for HOA/condo associations."""


# Tax rates
IL_REPLACEMENT_TAX_RATE = 0.025  # 2.5%
IL_INCOME_TAX_RATE = 0.07        # 7.0%


def calculate_il1120(financial_info):
    """Calculate all IL-1120 line values from federal financial_info dict.

    For HOAs, all income is inside Illinois so Step 4 (apportionment) is skipped.
    Line 1 = federal 1120-H Line 19 (taxable income after $100 deduction).

    Returns dict with line numbers as keys.
    """
    federal_taxable_income = max(0, financial_info.get('taxable_income', 0))

    # Step 2: Federal taxable income and additions
    line_1 = federal_taxable_income
    line_2 = line_1  # Same for HOAs (no separate Schedule M adjustments)
    line_3 = 0  # State/municipal interest excluded from Line 1
    line_4 = 0  # IL income/replacement tax deducted in arriving at Line 1
    line_5 = 0  # IL special depreciation (Form IL-4562)
    line_6 = 0  # Related party expenses (Schedule 80/20)
    line_7 = 0  # Distributive share additions (K-1-P or K-1-T)
    line_8 = 0  # Other additions (Schedule M)
    line_9 = line_2 + line_3 + line_4 + line_5 + line_6 + line_7 + line_8

    # Step 3: Subtractions (all zero for HOAs)
    line_10 = 0  # US Treasury/exempt federal obligations
    line_11 = 0  # River Edge / High Impact Business Zone credits
    line_12 = 0  # Enterprise Zone/Foreign Trade Zone/High Impact deductions
    line_13 = 0  # Contributions to certain job training
    line_14 = 0  # Historic preservation
    line_15 = 0  # Dividends from subsidiaries
    line_16 = 0  # Contribution deduction
    line_17 = 0  # Foreign dividend subtraction
    line_18 = 0  # IL special depreciation
    line_19 = 0  # Related party expenses
    line_20 = 0  # Distributive share subtractions
    line_21 = 0  # Other subtractions
    line_22 = sum([line_10, line_11, line_12, line_13, line_14, line_15,
                   line_16, line_17, line_18, line_19, line_20, line_21])
    line_23 = line_9 - line_22  # Base income

    # Step 4: Apportionment - SKIPPED for HOAs (all income in IL)
    # Check box A on Line 23 to indicate all income is in Illinois
    line_24 = 0
    line_25 = 0
    line_26 = 0
    line_27 = 0
    line_28 = 0
    line_29 = 0
    line_30_whole = 0
    line_30_decimal = 0
    line_31 = 0
    line_32 = 0
    line_33 = 0
    line_34 = 0

    # Step 5: Tax base
    line_35 = line_23  # Base income from Step 3
    line_36 = 0  # IL net loss deduction
    line_37 = line_35 - line_36
    line_38 = 0  # Merged losses
    line_39 = max(0, line_37 - line_38)

    # Step 6: Replacement tax (2.5%)
    line_40 = int(round(line_39 * IL_REPLACEMENT_TAX_RATE))
    line_41 = 0  # Recapture (Schedule 4255)
    line_42 = line_40 + line_41

    # Step 6 continued: Credits against replacement tax
    line_43 = 0  # Form IL-477 credits
    line_44 = max(0, line_42 - line_43)

    # Step 7: Income tax (7.0%)
    line_45 = int(round(line_39 * IL_INCOME_TAX_RATE))
    line_46 = 0  # Recapture (Schedule 4255)
    line_47 = line_45 + line_46

    # Step 7 continued: Credits against income tax
    line_48 = 0  # Schedule 1299-D credits
    line_49 = max(0, line_47 - line_48)

    # Step 7: Net taxes
    line_50 = line_44   # Replacement tax after credits
    line_51 = 0         # Surcharge
    line_52 = line_50 + line_51  # Net replacement tax
    line_53 = line_49   # Income tax after credits
    line_54 = 0         # Personal Property Tax Replacement Income Tax
    line_55 = line_53 + line_54  # Net income tax
    line_56 = 0         # Pass-through withholding
    line_57 = 0         # Compassionate Use of Medical Cannabis surcharge

    # Step 7: Total tax
    line_58 = line_52 + line_55 + line_56 + line_57
    line_59 = 0  # Interest/penalty
    line_60 = line_58 + line_59

    # Step 8: Payments and credits (all zero for HOAs)
    line_61a = 0  # Previous overpayments
    line_61b = 0  # Payments before filing
    line_61c = 0  # Pass-through entity payments (K-1-P)
    line_61d = 0  # Pass-through withholding (K-1-T)
    line_61e = 0  # W-2G amounts
    line_62 = line_61a + line_61b + line_61c + line_61d + line_61e
    line_63 = max(0, line_62 - line_60)  # Overpayment
    line_64 = 0  # Carryforward
    line_65 = max(0, line_63 - line_64)  # Refund
    line_67 = max(0, line_60 - line_62)  # Amount owed

    return {
        'line_1': line_1, 'line_2': line_2, 'line_3': line_3,
        'line_4': line_4, 'line_5': line_5, 'line_6': line_6,
        'line_7': line_7, 'line_8': line_8, 'line_9': line_9,
        'line_10': line_10, 'line_11': line_11, 'line_12': line_12,
        'line_13': line_13, 'line_14': line_14, 'line_15': line_15,
        'line_16': line_16, 'line_17': line_17, 'line_18': line_18,
        'line_19': line_19, 'line_20': line_20, 'line_21': line_21,
        'line_22': line_22, 'line_23': line_23,
        'line_24': line_24, 'line_25': line_25, 'line_26': line_26,
        'line_27': line_27, 'line_28': line_28, 'line_29': line_29,
        'line_30_whole': line_30_whole, 'line_30_decimal': line_30_decimal,
        'line_31': line_31, 'line_32': line_32, 'line_33': line_33,
        'line_34': line_34,
        'line_35': line_35, 'line_36': line_36, 'line_37': line_37,
        'line_38': line_38, 'line_39': line_39,
        'line_40': line_40, 'line_41': line_41, 'line_42': line_42,
        'line_43': line_43, 'line_44': line_44,
        'line_45': line_45, 'line_46': line_46, 'line_47': line_47,
        'line_48': line_48, 'line_49': line_49,
        'line_50': line_50, 'line_51': line_51, 'line_52': line_52,
        'line_53': line_53, 'line_54': line_54, 'line_55': line_55,
        'line_56': line_56, 'line_57': line_57,
        'line_58': line_58, 'line_59': line_59, 'line_60': line_60,
        'line_61a': line_61a, 'line_61b': line_61b, 'line_61c': line_61c,
        'line_61d': line_61d, 'line_61e': line_61e,
        'line_62': line_62, 'line_63': line_63, 'line_64': line_64,
        'line_65': line_65, 'line_67': line_67,
        'replacement_tax_rate': IL_REPLACEMENT_TAX_RATE,
        'income_tax_rate': IL_INCOME_TAX_RATE,
        'check_box_a': True,  # All income inside Illinois
    }
