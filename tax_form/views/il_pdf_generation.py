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
        'p0_amount_paying': (464, 655),     # rect [462.0, 653.0, 578.8, 666.5]
        'p0_name': (87, 590),               # rect [85.1, 588.3, 335.9, 601.8]
        'p0_address': (126, 543),            # rect [124.5, 541.6, 352.6, 555.1]
        'p0_city': (86, 525),               # rect [84.6, 523.7, 214.1, 537.2]
        'p0_state': (253, 526),              # rect [251.4, 524.0, 282.3, 537.5]
        'p0_zip': (312, 526),               # rect [310.5, 524.4, 355.7, 537.9]
        'p0_fein_prefix': (388, 611),        # rect [385.9, 609.1, 425.6, 622.6]
        'p0_fein_suffix': (433, 611),        # rect [431.2, 609.5, 570.5, 623.0]
        'p0_naics': (388, 529),              # rect [386.5, 527.9, 551.3, 541.4] (Line P)
        'p0_state_tax_id': (388, 488),       # rect [385.9, 485.9, 587.6, 499.4] (Line Q)
        'p0_records_city': (388, 425),       # rect [386.2, 422.9, 498.9, 436.4] (Line R city)
        'p0_records_state': (502, 425),      # rect [500.2, 422.7, 521.2, 436.2] (Line R state)
        'p0_records_zip': (525, 425),        # rect [522.9, 422.9, 588.5, 436.4] (Line R zip)
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
        'p2_preparer_date_month': (389, 88),     # rect [386.9, 86.8, 404.9, 100.0]
        'p2_preparer_date_day': (408, 88),       # rect [406.5, 86.8, 424.2, 100.0]
        'p2_preparer_date_year': (428, 88),      # rect [426.1, 86.8, 459.2, 100.0]
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

# Column widths for right-justification
IL_NUMERIC_COLUMN_WIDTHS = {
    # Page 1 right column (Lines 1-9, 22-23): rect width = 550 - 473.7 ≈ 76
    'p1_right': 75,
    # Page 1 left sub-column (Lines 10-21): rect width = 451 - 374.7 ≈ 76
    'p1_left': 75,
    # Page 2 right column: rect width = 562 - 485 ≈ 77
    'p2_right': 77,
    # Page 2 left sub-column (Lines 61a-61e): rect width = 449 - 372 ≈ 77
    'p2_left': 77,
    # Page 0 amount paying: rect width = 579 - 462 ≈ 117
    'p0_amount': 117,
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


def _right_justify_text(can, text, x, y, width):
    """Draw text right-justified within a box starting at x with given width."""
    text_width = pdfmetrics.stringWidth(text, 'Courier', 10)
    adjusted_x = x + width - text_width
    can.drawString(adjusted_x, y, text)


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
            elif key in IL_NUMERIC_FIELDS:
                can.setFont('Courier', 10)
                formatted = _format_number(value)
                col_width = _get_column_width(key)
                _right_justify_text(can, formatted, x, y, col_width)
            else:
                # Text fields (left-justified)
                can.setFont('Helvetica', 9)
                can.drawString(x, y, str(value) if value else '')

            logger.debug(f"IL-1120 page {page_idx}: {key}={value} at ({x},{y})")

        can.save()
        packet.seek(0)
        overlay = PdfReader(packet)
        template_page.merge_page(overlay.pages[0])
        pages.append(template_page)

    return pages
