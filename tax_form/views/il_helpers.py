"""Data preparation for IL-1120 PDF generation."""

from datetime import date
from ..il_calculations import calculate_il1120


def prepare_il1120_data(financial_info, association, preparer):
    """Prepare all IL-1120 data mapped to PDF field position keys.

    Returns dict keyed by field names with p0_, p1_, p2_ page prefixes.
    """
    il = calculate_il1120(financial_info)
    tax_year = financial_info.get('tax_year', 2024)

    # Split FEIN (format: "XX-XXXXXXX") into prefix and suffix
    ein = association.ein or ''
    ein_digits = ein.replace('-', '')
    fein_prefix = ein_digits[:2] if len(ein_digits) >= 2 else ein_digits
    fein_suffix = ein_digits[2:] if len(ein_digits) > 2 else ''

    # Split preparer phone into area code and number
    prep_phone = (preparer.firm_phone if preparer else '') or ''
    prep_phone_digits = ''.join(c for c in prep_phone if c.isdigit())
    if len(prep_phone_digits) == 10:
        prep_area_code = prep_phone_digits[:3]
        prep_phone_num = f'{prep_phone_digits[3:6]}-{prep_phone_digits[6:]}'
    elif len(prep_phone_digits) == 7:
        prep_area_code = ''
        prep_phone_num = f'{prep_phone_digits[:3]}-{prep_phone_digits[3:]}'
    else:
        prep_area_code = ''
        prep_phone_num = prep_phone

    today = date.today()

    data = {}

    # === Page 0: Step 1 - Identification ===
    data['p0_tax_year_begin_month'] = '01'
    data['p0_tax_year_begin_day'] = '01'
    data['p0_tax_year_begin_year'] = str(tax_year)
    data['p0_tax_year_end_month'] = '12'
    data['p0_tax_year_end_day'] = '31'
    data['p0_tax_year_end_year'] = str(tax_year)
    data['p0_amount_paying'] = il['line_67']  # Amount paying with return
    data['p0_name'] = association.association_name
    data['p0_address'] = association.mailing_address
    data['p0_city'] = association.city
    data['p0_state'] = association.state[:2].upper() if association.state else ''
    data['p0_zip'] = association.zipcode
    data['p0_fein_prefix'] = fein_prefix
    data['p0_fein_suffix'] = fein_suffix
    data['p0_naics'] = association.naics_code or ''
    data['p0_state_tax_id'] = association.state_tax_id or ''
    data['p0_records_city'] = association.records_city or ''
    data['p0_records_state'] = association.records_state or ''
    data['p0_records_zip'] = association.records_zip or ''
    data['p0_accrual'] = True  # Always accrual for HOAs

    # === Page 1: Steps 2-4 ===
    data['p1_line_1'] = il['line_1']
    data['p1_line_2'] = il['line_2']
    data['p1_line_3'] = il['line_3']
    data['p1_line_4'] = il['line_4']
    data['p1_line_5'] = il['line_5']
    data['p1_line_6'] = il['line_6']
    data['p1_line_7'] = il['line_7']
    data['p1_line_8'] = il['line_8']
    data['p1_line_9'] = il['line_9']
    data['p1_line_10'] = il['line_10']
    data['p1_line_11'] = il['line_11']
    data['p1_line_12'] = il['line_12']
    data['p1_line_13'] = il['line_13']
    data['p1_line_14'] = il['line_14']
    data['p1_line_15'] = il['line_15']
    data['p1_line_16'] = il['line_16']
    data['p1_line_17'] = il['line_17']
    data['p1_line_18'] = il['line_18']
    data['p1_line_19'] = il['line_19']
    data['p1_line_20'] = il['line_20']
    data['p1_line_21'] = il['line_21']
    data['p1_line_22'] = il['line_22']
    data['p1_line_23'] = il['line_23']
    data['p1_check_box_a'] = il['check_box_a']  # All income in IL

    # === Page 2: Steps 5-9 ===
    data['p2_line_35'] = il['line_35']
    data['p2_line_36'] = il['line_36']
    data['p2_line_37'] = il['line_37']
    data['p2_line_38'] = il['line_38']
    data['p2_line_39'] = il['line_39']
    data['p2_line_40'] = il['line_40']
    data['p2_line_41'] = il['line_41']
    data['p2_line_42'] = il['line_42']
    data['p2_line_43'] = il['line_43']
    data['p2_line_44'] = il['line_44']
    data['p2_line_45'] = il['line_45']
    data['p2_line_46'] = il['line_46']
    data['p2_line_47'] = il['line_47']
    data['p2_line_48'] = il['line_48']
    data['p2_line_49'] = il['line_49']
    data['p2_line_50'] = il['line_50']
    data['p2_line_51'] = il['line_51']
    data['p2_line_52'] = il['line_52']
    data['p2_line_53'] = il['line_53']
    data['p2_line_54'] = il['line_54']
    data['p2_line_55'] = il['line_55']
    data['p2_line_56'] = il['line_56']
    data['p2_line_57'] = il['line_57']
    data['p2_line_58'] = il['line_58']
    data['p2_line_59'] = il['line_59']
    data['p2_line_60'] = il['line_60']
    data['p2_line_61a'] = il['line_61a']
    data['p2_line_61b'] = il['line_61b']
    data['p2_line_61c'] = il['line_61c']
    data['p2_line_61d'] = il['line_61d']
    data['p2_line_61e'] = il['line_61e']
    data['p2_line_62'] = il['line_62']
    data['p2_line_63'] = il['line_63']
    data['p2_line_64'] = il['line_64']
    data['p2_line_65'] = il['line_65']
    data['p2_line_67'] = il['line_67']

    # Step 9: Preparer information
    data['p2_discuss_with_preparer'] = True
    data['p2_preparer_name'] = preparer.name if preparer else ''
    data['p2_preparer_signature'] = preparer.signature if preparer else ''
    data['p2_preparer_date_month'] = f'{today.month:02d}'
    data['p2_preparer_date_day'] = f'{today.day:02d}'
    data['p2_preparer_date_year'] = str(today.year)
    data['p2_preparer_ptin'] = preparer.ptin if preparer else ''
    data['p2_firm_name'] = preparer.firm_name if preparer else ''
    data['p2_firm_fein'] = preparer.firm_ein if preparer else ''
    data['p2_firm_address'] = preparer.firm_address if preparer else ''
    data['p2_firm_area_code'] = prep_area_code
    data['p2_firm_phone'] = prep_phone_num

    return data
