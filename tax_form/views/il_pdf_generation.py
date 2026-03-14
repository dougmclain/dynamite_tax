"""IL-1120 PDF generation - overlays data onto the blank IL-1120 template."""

import logging
from pathlib import Path
from io import BytesIO
from django.conf import settings
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from .il_helpers import prepare_il1120_data

logger = logging.getLogger(__name__)

# Field positions by year, keyed as {year: {field_name: (x, y)}}
# Coordinates derived from annotation rectangles: x = rect_left + 2, y = rect_bottom + 2
# For right-justified numerics, x is the rect_left (right-justification handled by render logic)
IL_FIELD_POSITIONS_BY_YEAR = {
    2025: {
        # === Page 0: Step 1 - Identification ===
        'p0_tax_year_begin_month': (109, 678),
        'p0_tax_year_begin_day': (138, 678),
        'p0_tax_year_begin_year': (178, 678),
        'p0_tax_year_end_month': (238, 678),
        'p0_tax_year_end_day': (267, 678),
        'p0_tax_year_end_year': (309, 678),
        'p0_amount_paying': (464, 657),     # rect [462.0, 653.0, 578.8, 666.5] — raised 2pt
        'p0_name': (87, 592),               # rect [85.1, 588.3, 335.9, 601.8] — raised 2pt off line
        'p0_care_of': (86, 561),            # C/O line — lowered 2pt (was too high)
        'p0_address': (126, 545),            # rect [124.5, 541.6, 352.6, 555.1] — raised 2pt off line
        'p0_city': (86, 528),               # rect [84.6, 523.7, 214.1, 537.2] — raised 3pt off line
        'p0_state': (258, 529),              # rect [251.4, 524.0, 282.3, 537.5] — raised 3pt off line
        'p0_zip': (318, 529),               # rect [310.5, 524.4, 355.7, 537.9] — raised 3pt off line
        'p0_fein_prefix': (386, 613),        # rect [385.9, 609.1, 425.6, 622.6] — raised 2pt
        'p0_fein_suffix': (431, 613),        # rect [431.2, 609.5, 570.5, 623.0] — raised 2pt
        'p0_naics': (386, 531),              # rect [386.5, 527.9, 551.3, 541.4] (Line P) — raised 2pt
        'p0_state_tax_id': (388, 490),       # rect [385.9, 485.9, 587.6, 499.4] (Line Q) — raised 2pt
        'p0_records_city': (388, 427),       # rect [386.2, 422.9, 498.9, 436.4] (Line R city) — raised 2pt
        'p0_records_state': (502, 427),      # rect [500.2, 422.7, 521.2, 436.2] (Line R state) — raised 2pt
        'p0_records_zip': (525, 427),        # rect [522.9, 422.9, 588.5, 436.4] (Line R zip) — raised 2pt
        'p0_accrual': (434, 341),            # rect [432.7, 339.8, 444.5, 351.4]

        # === Page 1: Steps 2-4 ===
        # Right column (Lines 1-9): rect right edge ~550, width ~76
        'p1_line_1': (475, 706),             # rect [473.7, 704.0, 550.0, 719.3]
        'p1_line_2': (475, 691),             # rect [473.7, 689.1, 550.0, 704.4]
        'p1_line_3': (475, 676),             # rect [473.7, 674.1, 550.0, 689.4]
        'p1_line_4': (475, 661),             # rect [473.7, 659.2, 550.0, 674.5]
        'p1_line_5': (475, 646),             # rect [473.7, 644.2, 550.0, 659.5]
        'p1_line_6': (475, 631),             # rect [473.7, 629.3, 550.0, 644.6]
        'p1_line_7': (475, 617),             # rect [473.7, 615.1, 550.0, 628.8]
        'p1_line_8': (475, 602),             # rect [473.7, 600.3, 550.0, 613.7]
        'p1_line_9': (475, 587),             # rect [473.7, 585.7, 550.0, 598.4]
        # Left sub-column (Lines 10-21): rect right edge ~451, width ~76
        'p1_line_10': (376, 553),            # rect [374.7, 551.7, 451.0, 567.0]
        'p1_line_11': (376, 525),            # rect [374.7, 523.2, 451.0, 538.5]
        'p1_line_12': (376, 500),            # rect [374.4, 497.9, 450.8, 513.3]
        'p1_line_13': (376, 484),            # rect [374.4, 482.7, 450.8, 498.0]
        'p1_line_14': (376, 469),            # rect [374.4, 467.5, 450.8, 482.8]
        'p1_line_15': (376, 454),            # rect [374.4, 452.2, 450.8, 467.5]
        'p1_line_16': (376, 439),            # rect [374.4, 437.0, 450.8, 452.3]
        'p1_line_17': (376, 423),            # rect [374.4, 421.8, 450.8, 437.1]
        'p1_line_18': (376, 408),            # rect [374.4, 406.5, 450.8, 421.8]
        'p1_line_19': (376, 393),            # rect [374.4, 391.3, 450.8, 406.6]
        'p1_line_20': (376, 378),            # rect [374.4, 376.0, 450.8, 391.3]
        'p1_line_21': (376, 362),            # rect [374.4, 360.8, 450.8, 376.1]
        # Right column again
        'p1_line_22': (475, 351),            # rect [473.8, 349.2, 549.8, 364.5]
        'p1_line_23': (475, 335),            # rect [473.8, 333.0, 549.8, 348.3]
        # Check box A (all income in IL) - skip Step 4
        'p1_check_box_a': (569, 310),        # rect [567.6, 308.8, 579.4, 321.7]

        # === Page 2: Steps 5-9 ===
        # Right column: rect right edge ~562, width ~77
        'p2_line_35': (486, 729),            # rect [484.8, 727.2, 561.9, 739.9]
        'p2_line_36': (486, 715),            # rect [484.8, 713.9, 561.9, 726.6]
        'p2_line_37': (486, 702),            # rect [484.8, 700.2, 561.9, 712.9]
        'p2_line_38': (486, 681),            # rect [484.8, 679.4, 561.9, 692.1]
        'p2_line_39': (486, 667),            # rect [484.8, 665.8, 561.9, 678.5]
        'p2_line_40': (486, 644),            # rect [484.8, 642.0, 561.9, 654.7]
        'p2_line_41': (486, 630),            # rect [484.8, 628.8, 561.9, 641.5]
        'p2_line_42': (486, 618),            # rect [484.8, 616.0, 561.9, 628.7]
        'p2_line_43': (486, 604),            # rect [484.8, 602.8, 561.9, 615.5]
        'p2_line_44': (486, 592),            # rect [484.8, 590.4, 561.9, 603.1]
        'p2_line_45': (486, 569),            # rect [484.8, 567.7, 561.9, 580.4]
        'p2_line_46': (486, 556),            # rect [484.8, 554.6, 561.9, 567.3]
        'p2_line_47': (486, 543),            # rect [484.8, 541.5, 561.9, 554.2]
        'p2_line_48': (486, 530),            # rect [484.8, 528.3, 561.9, 541.0]
        'p2_line_49': (486, 517),            # rect [484.8, 515.8, 561.9, 528.5]
        'p2_line_50': (486, 494),            # rect [484.8, 492.2, 561.9, 504.3]
        'p2_line_51': (486, 481),            # rect [484.8, 479.1, 561.9, 491.3]
        'p2_line_52': (486, 468),            # rect [484.8, 466.6, 561.9, 478.2]
        'p2_line_53': (486, 455),            # rect [484.8, 453.5, 561.9, 465.1]
        'p2_line_54': (486, 443),            # rect [484.8, 441.1, 561.9, 452.0]
        'p2_line_55': (486, 429),            # rect [484.8, 427.6, 561.9, 439.0]
        'p2_line_56': (486, 417),            # rect [484.8, 415.4, 561.9, 426.1]
        'p2_line_57': (486, 405),            # rect [484.8, 403.2, 561.9, 413.9]
        'p2_line_58': (486, 391),            # rect [484.8, 389.5, 561.9, 400.3]
        'p2_line_59': (486, 379),            # rect [485.0, 377.1, 562.0, 387.2]
        'p2_line_60': (486, 367),            # rect [485.0, 365.1, 562.0, 375.2]
        # Left sub-column (Lines 61a-61e): rect right edge ~449, width ~77
        'p2_line_61a': (373, 343),           # rect [371.6, 341.7, 448.7, 354.4]
        'p2_line_61b': (373, 330),           # rect [371.6, 328.5, 448.7, 341.2]
        'p2_line_61c': (373, 308),           # rect [371.6, 306.2, 448.7, 318.9]
        'p2_line_61d': (373, 285),           # rect [371.6, 283.2, 448.7, 295.9]
        'p2_line_61e': (373, 272),           # rect [371.6, 270.4, 448.7, 283.1]
        # Right column again
        'p2_line_62': (487, 262),            # rect [485.2, 260.3, 562.3, 273.0]
        'p2_line_63': (487, 248),            # rect [485.2, 246.1, 562.3, 258.8]
        'p2_line_64': (487, 226),            # rect [485.2, 224.2, 562.3, 236.9]
        'p2_line_65': (487, 213),            # rect [485.2, 211.2, 562.3, 223.9]
        'p2_line_67': (487, 152),            # rect [485.2, 150.5, 562.3, 163.2]

        # Step 9: Preparer section
        'p2_discuss_with_preparer': (479, 122),  # rect [477.3, 120.6, 488.3, 131.9]
        'p2_preparer_name': (75, 89),            # rect [73.6, 87.1, 236.5, 99.1]
        'p2_preparer_signature': (240, 89),      # Between name (ends ~236) and date (starts ~387)
        'p2_preparer_date': (389, 88),             # Single date field with slashes (MM/DD/YYYY)
        'p2_preparer_ptin': (515, 88),           # rect [513.5, 86.3, 589.1, 99.6]
        'p2_firm_name': (150, 62),               # rect [147.9, 59.9, 438.4, 73.4]
        'p2_firm_fein': (498, 62),               # rect [496.0, 60.6, 590.9, 73.8]
        'p2_firm_address': (150, 47),            # rect [147.9, 45.5, 438.4, 59.0]
        'p2_firm_area_code': (502, 47),          # rect [500.0, 45.8, 522.3, 59.3]
        'p2_firm_phone': (526, 47),              # rect [524.3, 45.8, 590.9, 59.3]
    },
}

# Numeric fields that should be right-justified
IL_NUMERIC_FIELDS = {
    'p0_amount_paying',
    # Page 1 lines
    'p1_line_1', 'p1_line_2', 'p1_line_3', 'p1_line_4', 'p1_line_5',
    'p1_line_6', 'p1_line_7', 'p1_line_8', 'p1_line_9',
    'p1_line_10', 'p1_line_11', 'p1_line_12', 'p1_line_13', 'p1_line_14',
    'p1_line_15', 'p1_line_16', 'p1_line_17', 'p1_line_18', 'p1_line_19',
    'p1_line_20', 'p1_line_21', 'p1_line_22', 'p1_line_23',
    # Page 2 lines
    'p2_line_35', 'p2_line_36', 'p2_line_37', 'p2_line_38', 'p2_line_39',
    'p2_line_40', 'p2_line_41', 'p2_line_42', 'p2_line_43', 'p2_line_44',
    'p2_line_45', 'p2_line_46', 'p2_line_47', 'p2_line_48', 'p2_line_49',
    'p2_line_50', 'p2_line_51', 'p2_line_52', 'p2_line_53', 'p2_line_54',
    'p2_line_55', 'p2_line_56', 'p2_line_57', 'p2_line_58', 'p2_line_59',
    'p2_line_60',
    'p2_line_61a', 'p2_line_61b', 'p2_line_61c', 'p2_line_61d', 'p2_line_61e',
    'p2_line_62', 'p2_line_63', 'p2_line_64', 'p2_line_65', 'p2_line_67',
}

# Checkbox fields
IL_CHECKBOX_FIELDS = {
    'p0_accrual',
    'p1_check_box_a',
    'p2_discuss_with_preparer',
}

# Fields where each character is drawn individually with fixed spacing (e.g., digit boxes)
IL_SPACED_CHAR_FIELDS = {
    'p0_fein_prefix': 20,   # 2 digits in ~40pt: 40/2 = 20pt per slot
    'p0_fein_suffix': 20,   # 7 digits in ~139pt: 139/7 ≈ 20pt per slot
    'p0_naics': 27,         # 6 digits in ~165pt: 165/6 ≈ 27pt per slot
}

# Column widths for right-justification (slightly inside rect right edge)
IL_NUMERIC_COLUMN_WIDTHS = {
    # Page 1 right column (Lines 1-9, 22-23): rect [473.7 .. 550.0]
    'p1_right': 73,
    # Page 1 left sub-column (Lines 10-21): rect [374.7 .. 451.0]
    'p1_left': 73,
    # Page 2 right column: rect [484.8 .. 561.9]
    'p2_right': 75,
    # Page 2 left sub-column (Lines 61a-61e): rect [371.6 .. 448.7]
    'p2_left': 75,
    # Page 0 amount paying: rect [462.0 .. 578.8]
    'p0_amount': 115,
}

# Map field to its column width
def _get_column_width(field_name):
    if field_name.startswith('p0_'):
        return IL_NUMERIC_COLUMN_WIDTHS['p0_amount']
    elif field_name.startswith('p1_line_') and field_name in IL_NUMERIC_FIELDS:
        line_num = field_name.replace('p1_line_', '')
        try:
            n = int(line_num)
            if 10 <= n <= 21:
                return IL_NUMERIC_COLUMN_WIDTHS['p1_left']
        except ValueError:
            pass
        return IL_NUMERIC_COLUMN_WIDTHS['p1_right']
    elif field_name.startswith('p2_line_61'):
        return IL_NUMERIC_COLUMN_WIDTHS['p2_left']
    elif field_name.startswith('p2_'):
        return IL_NUMERIC_COLUMN_WIDTHS['p2_right']
    return 75  # default


def _format_number(value):
    """Format a number with commas."""
    if value is None or value == '':
        return ''
    try:
        return f"{int(float(value)):,}"
    except (ValueError, TypeError):
        return str(value)


def _format_number_with_cents(value):
    """Format a number with commas and two decimal places."""
    if value is None or value == '':
        return ''
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)


# Fields that should display with cents (e.g., 0.00)
IL_CENTS_FIELDS = {'p0_amount_paying'}


def _right_justify_text(can, text, x, y, width):
    """Draw text right-justified within a box starting at x with given width."""
    text_width = pdfmetrics.stringWidth(text, 'Courier', 10)
    adjusted_x = x + width - text_width
    can.drawString(adjusted_x, y, text)


def _draw_spaced_chars(can, text, x, y, spacing):
    """Draw each character centered in evenly spaced slots."""
    can.setFont('Courier', 10)
    char_width = pdfmetrics.stringWidth('0', 'Courier', 10)
    for i, ch in enumerate(text):
        # Center each character within its slot
        slot_x = x + i * spacing + (spacing - char_width) / 2
        can.drawString(slot_x, y, ch)


def _find_il_template(tax_year):
    """Find the IL-1120 template PDF, checking multiple paths."""
    template_name = f'template_il1120_{tax_year}.pdf'
    possible_paths = [
        settings.PDF_TEMPLATE_DIR / template_name,
        Path('/var/lib/render/disk/pdf_templates') / template_name,
        Path('/media/pdf_templates') / template_name,
        Path('/data/pdf_templates') / template_name,
        Path(settings.BASE_DIR) / 'pdf_templates' / template_name,
        Path(settings.BASE_DIR) / 'tax_form' / 'pdf_templates' / template_name,
    ]
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found IL-1120 template at: {path}")
            return path
    logger.error(f"IL-1120 template not found. Searched: {possible_paths}")
    raise FileNotFoundError(f"IL-1120 template not found for year {tax_year}")


def generate_il1120_pages(financial_info, association, preparer, tax_year):
    """Generate IL-1120 pages and return list of PyPDF2 page objects.

    Returns list of 3 page objects ready to be appended to a PdfWriter.
    """
    template_path = _find_il_template(tax_year)
    reader = PdfReader(str(template_path))

    positions = IL_FIELD_POSITIONS_BY_YEAR.get(int(tax_year), IL_FIELD_POSITIONS_BY_YEAR[2025])
    data = prepare_il1120_data(financial_info, association, preparer)

    # Group fields by page prefix
    page_fields = {'p0': {}, 'p1': {}, 'p2': {}}
    for key, value in data.items():
        prefix = key[:2]
        if prefix in page_fields:
            page_fields[prefix][key] = value

    pages = []
    for page_idx, prefix in enumerate(['p0', 'p1', 'p2']):
        template_page = reader.pages[page_idx]

        # Create overlay canvas
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        for key, value in page_fields[prefix].items():
            if key not in positions:
                continue
            x, y = positions[key]

            if key in IL_CHECKBOX_FIELDS:
                if value:
                    can.setFont('Helvetica', 10)
                    can.drawString(x, y, 'X')
            elif key in IL_SPACED_CHAR_FIELDS:
                text = str(value) if value else ''
                if text:
                    _draw_spaced_chars(can, text, x, y, IL_SPACED_CHAR_FIELDS[key])
            elif key in IL_NUMERIC_FIELDS:
                can.setFont('Courier', 10)
                if key in IL_CENTS_FIELDS:
                    formatted = _format_number_with_cents(value)
                else:
                    formatted = _format_number(value)
                col_width = _get_column_width(key)
                _right_justify_text(can, formatted, x, y, col_width)
            else:
                # Text fields (left-justified)
                can.setFont('Helvetica', 10)
                can.drawString(x, y, str(value) if value else '')

            logger.debug(f"IL-1120 page {page_idx}: {key}={value} at ({x},{y})")

        can.save()
        packet.seek(0)
        overlay = PdfReader(packet)
        template_page.merge_page(overlay.pages[0])
        pages.append(template_page)

    return pages


# === IL-1120-V Payment Voucher ===

# Field positions derived from annotation rectangles on the voucher page
# Convention: x = rect_left + 2, y = rect_bottom + 2
IL_VOUCHER_FIELD_POSITIONS = {
    'fein_prefix': (88, 172),       # rect [86.3, 170.0, 122.0, 188.5]
    'fein_suffix': (130, 172),      # rect [128.3, 170.0, 251.4, 188.5]
    'name': (89, 144),              # rect [86.7, 142.1, 342.7, 160.6]
    'care_of': (89, 120),           # rect [86.7, 118.2, 342.7, 136.7]
    'address': (89, 95),            # rect [86.7, 92.9, 342.7, 111.4]
    'city': (88, 72),               # rect [86.3, 69.9, 201.3, 88.4]
    'state': (239, 72),             # rect [237.1, 69.9, 268.5, 88.4]
    'zip': (293, 72),               # rect [291.4, 69.9, 342.7, 88.4]
    'area_code': (88, 48),          # rect [86.0, 46.3, 123.6, 64.8]
    'phone': (133, 48),             # rect [130.6, 46.3, 221.8, 64.8]
    'tax_year_end_month': (441, 159),  # rect [439.1, 156.6, 471.8, 175.1]
    'tax_year_end_year': (512, 159),   # rect [509.8, 156.6, 542.6, 175.1]
    'payment_amount': (413, 121),      # rect [411.0, 119.2, 527.2, 137.7]
}

IL_VOUCHER_SPACED_CHAR_FIELDS = {
    'fein_prefix': 18,   # 2 digits in ~36pt
    'fein_suffix': 18,   # 7 digits in ~123pt
}

IL_VOUCHER_NUMERIC_FIELDS = {'payment_amount'}
IL_VOUCHER_NUMERIC_WIDTH = 114  # rect width: 527.2 - 411.0 = 116.2


def _find_il_voucher_template(tax_year):
    """Find the IL-1120-V template PDF."""
    template_name = f'template_il1120v_{tax_year}.pdf'
    possible_paths = [
        settings.PDF_TEMPLATE_DIR / template_name,
        Path('/var/lib/render/disk/pdf_templates') / template_name,
        Path('/media/pdf_templates') / template_name,
        Path('/data/pdf_templates') / template_name,
        Path(settings.BASE_DIR) / 'pdf_templates' / template_name,
        Path(settings.BASE_DIR) / 'tax_form' / 'pdf_templates' / template_name,
    ]
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found IL-1120-V template at: {path}")
            return path
    logger.error(f"IL-1120-V template not found. Searched: {possible_paths}")
    raise FileNotFoundError(f"IL-1120-V template not found for year {tax_year}")


def generate_il1120v_page(financial_info, association, tax_year):
    """Generate a filled IL-1120-V payment voucher page.

    Returns a single PyPDF2 page object ready to append to a PdfWriter.
    Only call this when the IL-1120 line 67 (amount owed) > 0.
    """
    template_path = _find_il_voucher_template(tax_year)
    reader = PdfReader(str(template_path))
    template_page = reader.pages[0]

    # Prepare voucher data
    ein = (association.ein or '').replace('-', '')
    fein_prefix = ein[:2] if len(ein) >= 2 else ein
    fein_suffix = ein[2:] if len(ein) > 2 else ''

    # C/O: use state_care_of override, else management company name
    care_of = ''
    if hasattr(association, 'state_care_of') and association.state_care_of:
        care_of = association.state_care_of
    elif not association.is_self_managed and association.management_company:
        care_of = association.management_company.name

    # Phone: management company phone if available
    phone_raw = ''
    if not association.is_self_managed and association.management_company:
        phone_raw = association.management_company.phone or ''
    phone_digits = ''.join(c for c in phone_raw if c.isdigit())
    if len(phone_digits) == 10:
        area_code = phone_digits[:3]
        phone_num = f'{phone_digits[3:6]}-{phone_digits[6:]}'
    elif len(phone_digits) == 7:
        area_code = ''
        phone_num = f'{phone_digits[:3]}-{phone_digits[3:]}'
    else:
        area_code = ''
        phone_num = phone_raw

    # Tax year ending: fiscal year end month / year
    end_month = association.fiscal_year_end_month or 12
    tax_year_end_month = f'{end_month:02d}'
    tax_year_end_year = str(tax_year)

    # Payment amount from IL calculations
    from ..il_calculations import calculate_il1120
    il = calculate_il1120(financial_info)
    payment_amount = il.get('line_67', 0)

    data = {
        'fein_prefix': fein_prefix,
        'fein_suffix': fein_suffix,
        'name': association.association_name or '',
        'care_of': care_of,
        'address': association.mailing_address or '',
        'city': association.city or '',
        'state': (association.state or '')[:2].upper(),
        'zip': association.zipcode or '',
        'area_code': area_code,
        'phone': phone_num,
        'tax_year_end_month': tax_year_end_month,
        'tax_year_end_year': tax_year_end_year,
        'payment_amount': payment_amount,
    }

    # Create overlay
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    for key, value in data.items():
        if key not in IL_VOUCHER_FIELD_POSITIONS:
            continue
        x, y = IL_VOUCHER_FIELD_POSITIONS[key]

        if key in IL_VOUCHER_SPACED_CHAR_FIELDS:
            text = str(value) if value else ''
            if text:
                _draw_spaced_chars(can, text, x, y, IL_VOUCHER_SPACED_CHAR_FIELDS[key])
        elif key in IL_VOUCHER_NUMERIC_FIELDS:
            can.setFont('Courier', 10)
            formatted = _format_number_with_cents(value)
            _right_justify_text(can, formatted, x, y, IL_VOUCHER_NUMERIC_WIDTH)
        else:
            can.setFont('Helvetica', 10)
            can.drawString(x, y, str(value) if value else '')

    can.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    template_page.merge_page(overlay.pages[0])
    return template_page
