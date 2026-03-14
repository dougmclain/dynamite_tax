import os
import logging
from pathlib import Path
from datetime import date
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, TextStringObject, BooleanObject, NumberObject, ArrayObject
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from ..models import Financial, Association, Preparer
from .helpers import format_number, get_statement_details, prepare_pdf_data
from .instructions_generationg import InstructionsGenerator
from .il_pdf_generation import generate_il1120_pages, generate_il1120v_page

logger = logging.getLogger(__name__)

__all__ = ['generate_pdf']

# Update the pdf_generation.py file to standardize tax return filenames

def generate_pdf(financial_info, association, preparer, tax_year):
    """Generate PDF and return HTTP response."""
    # Create a list of possible template locations
    template_name = f'template_1120h_{tax_year}.pdf'
    possible_paths = [
        settings.PDF_TEMPLATE_DIR / template_name,
        Path('/var/lib/render/disk/pdf_templates') / template_name,
        Path('/media/pdf_templates') / template_name,
        Path('/data/pdf_templates') / template_name,
        Path(settings.BASE_DIR) / 'pdf_templates' / template_name,
        Path(settings.BASE_DIR) / 'tax_form' / 'pdf_templates' / template_name,
    ]
    
    # Try each path until we find one that exists
    template_path = None
    for path in possible_paths:
        logger.info(f"Checking for template at: {path}")
        if path.exists():
            template_path = path
            logger.info(f"Found template at: {path}")
            break
    
    # If no template is found, use the first path for error reporting
    if template_path is None:
        template_path = possible_paths[0]
        logger.error(f"PDF template not found at any of the searched locations")
        logger.error(f"Searched paths: {possible_paths}")
        raise FileNotFoundError(f"PDF template not found at {template_path} or any alternative locations")
    
    # Create a standardized filename with first 10 letters of association name, 1120H, and tax year
    assoc_name_safe = ''.join(c for c in association.association_name[:10] if c.isalnum())
    filing_state = association.get_filing_state()
    state_suffix = f'_IL1120' if filing_state == 'IL' else ''
    output_filename = f'{assoc_name_safe}_1120H{state_suffix}_{tax_year}.pdf'
    
    # Generate output path
    output_dir = settings.PDF_TEMP_DIR
    output_path = output_dir / output_filename
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Using output path: {output_path}")

    try:
        # Generate the PDF locally first
        generate_1120h_pdf(financial_info, association, preparer, str(template_path), str(output_path), tax_year=tax_year)
        
        if settings.USE_AZURE_STORAGE:
            # Upload to Azure Storage with the standardized filename
            azure_path = f'tax_returns/{output_filename}'
            
            # Read the generated PDF
            with open(output_path, 'rb') as f:
                file_content = f.read()
            
            # Save to Azure Storage
            azure_file_path = default_storage.save(azure_path, ContentFile(file_content))
            logger.info(f"PDF saved to Azure Storage at: {azure_file_path}")
            
            # Return the PDF as a response (from the local file)
            with open(output_path, 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={output_filename}'
                
            # Clean up local file
            try:
                os.remove(output_path)
                logger.info(f"Temporary PDF file removed: {output_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file: {str(e)}")
        else:
            # Local file handling (unchanged)
            with open(output_path, 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={output_filename}'
            
            # Clean up the temporary file
            try:
                os.remove(output_path)
                logger.info(f"Temporary PDF file removed: {output_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file: {str(e)}")
        
        return response
    except PermissionError:
        logger.error(f"Permission denied when writing to {output_path}")
        raise PermissionError(f"Permission denied when writing to {output_path}. Please check directory permissions.")
    except Exception as e:
        logger.error(f"Error in PDF generation: {str(e)}", exc_info=True)
        raise

FIELD_POSITIONS_BY_YEAR = {
    2024: {
        'f1_1': (75, 675),   # Name
        'f1_2': (450, 675),  # Employer identification number
        'f1_3': (75, 650),   # Number, street, and room or suite no.
        'f1_4': (75, 627),   # City or town, state or province, country, and ZIP
        'f1_5': (450, 627),  # Date association formed
        'name_change': (227, 615),      # Name change checkbox
        'address_change': (357, 615),  # Address change checkbox
        'condo': (213, 602),            # Condominium management association checkbox
        'homeowners': (357, 602),      # Residential real estate association checkbox
        'f1_6': (495, 590),  # B Total exempt function income
        'f1_7': (495, 578),  # C Total expenditures (90% test)
        'f1_8': (495, 566),  # D Association's total expenditures
        'f1_9': (495, 530),  # 1 Dividends
        'f1_10': (495, 518), # 2 Taxable interest
        'f1_11': (495, 506), # 3 Gross rents
        'f1_15': (495, 458), # 7 Other income
        'f1_16': (495, 446), # 8 Gross income
        'f1_23': (495, 350), # 15 Other deductions
        'f1_24': (495, 338), # 16 Total deductions
        'f1_25': (495, 326),  # 17 Taxable income before specific deduction
        'f1_27': (495, 290),  # 19 Taxable income
        'f1_28': (495, 278),   # 20 Tax (30% of line 19)
        'f1_30': (495, 254), # 22 Total tax
        'f1_31': (395, 230), # 23b Current year's estimated tax payments
        'f1_32': (395, 218), # 23c Tax deposited with Form 7004
        'f1_35': (495, 170), # 23g Total payments and credits
        'f1_36': (495, 158), # 24 Amount owed
        'f1_37': (495, 146), # 25 Overpayment
        'f1_38': (495, 134), # 26 Refunded
        'f1_39': (100, 62),  # Preparer's name
        'f1_40': (520, 62), # Preparer's PTIN
        'f1_41': (145, 50),  # Firm's name
        'f1_42': (500, 50), # Firm's EIN
        'f1_43': (145, 38),  # Firm's address
        'f1_44': (500, 38), # Firm's phone number
        'f1_45': (410, 62),  # Date
        'f1_46': (270, 62), # Preparer's signature
    },
    2025: {
        # Header fields - 2025 form separates City, State, Country, ZIP
        'f1_1': (126, 686),   # Name [rect 124,684,459,698]
        'f1_2': (464, 686),   # EIN [rect 462,684,576,698]
        'f1_3': (126, 662),   # Street address [rect 124,660,365,674]
        'f1_3_suite': (371, 662),  # Room/suite [rect 369,660,459,674]
        'f1_4_city': (126, 639),   # City [rect 124,637,236,650]
        'f1_4_state': (242, 639),  # State [rect 240,637,300,650]
        'f1_4_zip': (371, 639),    # ZIP [rect 369,637,459,650]
        'f1_5': (464, 638),   # Date formed [rect 462,636,576,648]
        # Checkboxes - 2025 stacks (1)-(4) vertically on left
        'name_change': (55, 676),       # (2) Name change [rect 53,674,61,682]
        'address_change': (55, 664),    # (3) Address change [rect 53,662,61,670]
        'amended_return': (55, 652),    # (4) Amended return
        'condo': (214, 628),            # Condominium [rect 212,626,220,634]
        'homeowners': (358, 628),       # Residential real estate [rect 356,626,364,634]
        # Right column numeric (right-justified, x=496 so right edge=576)
        'f1_6': (496, 614),   # B Total exempt function income [rect 504,612,576,624]
        'f1_7': (496, 602),   # C Total expenditures 90% test [rect 504,600,576,612]
        'f1_8': (496, 590),   # D Total expenditures [rect 504,588,576,600]
        'f1_9': (496, 566),   # 1 Dividends [rect 504,564,576,576]
        'f1_10': (496, 554),  # 2 Taxable interest [rect 504,552,576,564]
        'f1_11': (496, 542),  # 3 Gross rents [rect 504,540,576,552]
        'f1_15': (496, 494),  # 7 Other income [rect 504,492,576,504]
        'f1_16': (496, 482),  # 8 Gross income [rect 504,480,576,492]
        'f1_23': (496, 398),  # 15 Other deductions [rect 504,396,576,408]
        'f1_24': (496, 386),  # 16 Total deductions [rect 504,384,576,396]
        'f1_25': (496, 374),  # 17 Taxable income before $100 [rect 504,372,576,384]
        'f1_27': (496, 350),  # 19 Taxable income [rect 504,348,576,360]
        'f1_28': (496, 338),  # 20 Tax 30% [rect 504,336,576,348]
        'f1_30': (496, 314),  # 22 Total tax [rect 504,312,576,324]
        # Sub-column 23b-23c (right-justified, x=402 so right edge=482)
        'f1_31': (402, 290),  # 23b Estimated payments [rect 410,288,482,300]
        'f1_32': (402, 278),  # 23c Form 7004 [rect 410,276,482,288]
        # Main column again
        'f1_35': (496, 230),  # 23g Total payments [rect 504,228,576,240]
        'f1_36': (496, 218),  # 24 Amount owed [rect 504,216,576,228]
        'f1_37': (496, 206),  # 25 Overpayment [rect 504,204,576,216]
        'f1_38': (496, 194),  # 26b Refunded [rect 504,192,576,204]
        # Preparer section (left-justified strings)
        'f1_39': (97, 86),    # Preparer name [rect 95,84,244,98]
        'f1_40': (520, 86),   # PTIN [rect 518,84,576,98]
        'f1_41': (143, 74),   # Firm name [rect 141,72,460,84]
        'f1_42': (506, 74),   # Firm EIN [rect 504,72,576,84]
        'f1_43': (151, 62),   # Firm address [rect 149,60,460,72]
        'f1_44': (506, 62),   # Phone [rect 504,60,576,72]
        'f1_45': (412, 86),   # Date
        'f1_46': (270, 86),   # Preparer signature
    },
}

# Default to 2024 for backward compatibility
FIELD_POSITIONS = FIELD_POSITIONS_BY_YEAR[2024]

NUMERIC_COLUMN_WIDTH = 80  # width in points

def right_justify_text(can, text, x, y, width):
    text_width = pdfmetrics.stringWidth(text, 'Courier', 10)
    adjusted_x = x + width - text_width
    can.drawString(adjusted_x, y, text)

def generate_1120h_pdf(financial_info, association, preparer, template_path, output_path, tax_year=None):
    """Generate PDF and return HTTP response."""
    try:
        reader = PdfReader(template_path)
        writer = PdfWriter()

        # Pre-compute IL amounts for instructions page (if applicable)
        il_amount_owed = 0
        il_refund = 0
        try:
            if association.get_filing_state() == 'IL':
                from ..il_calculations import calculate_il1120
                il_calc = calculate_il1120(financial_info)
                il_amount_owed = il_calc.get('line_67', 0) or 0
                il_refund = il_calc.get('line_65', 0) or 0
        except Exception as e:
            logger.warning(f"Could not pre-compute IL amounts: {e}")

        # Generate and add instructions page
        instructions_generator = InstructionsGenerator()
        instructions_page = instructions_generator.generate_page(
            financial_info,
            association,
            amount_owed=financial_info.get('amount_owed', 0),
            refund_amount=financial_info.get('refunded', 0),
            il_amount_owed=il_amount_owed,
            il_refund=il_refund,
        )
        writer.add_page(instructions_page)

        # Select field positions based on tax year (explicit param takes priority)
        if tax_year is None:
            tax_year = financial_info.get('tax_year', 2024)
        tax_year = int(tax_year)
        positions = FIELD_POSITIONS_BY_YEAR.get(tax_year, FIELD_POSITIONS_BY_YEAR[2024])

        # Add the form page
        page = reader.pages[0]
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        data = prepare_pdf_data(financial_info, association, preparer)
        for key, value in data.items():
            if key in positions:
                x, y = positions[key]
                if isinstance(value, bool):
                    # Handle checkboxes
                    if value:
                        can.setFont('Helvetica', 10)
                        can.drawString(x, y, 'X')
                    # Do nothing if the value is False
                elif isinstance(value, (int, float)):
                    # Format and right-justify numeric values
                    can.setFont('Courier', 10)  # Use built-in Courier font for numbers
                    formatted_value = format_number(value)
                    right_justify_text(can, formatted_value, x, y, NUMERIC_COLUMN_WIDTH)
                else:
                    # Draw other fields normally
                    can.setFont('Helvetica', 10)
                    can.drawString(x, y, str(value))
                
                logger.debug(f"Drew field {key} with value {value} at position ({x}, {y})")

        can.save()
        packet.seek(0)
        overlay_bytes = packet.read()  # Save overlay for potential IL attachment copy
        new_pdf = PdfReader(BytesIO(overlay_bytes))
        page.merge_page(new_pdf.pages[0])
        writer.add_page(page)

        # Add statement page if needed
        if financial_info.get('total_other_income', 0) > 0 or financial_info.get('other_deductions', 0) > 0:
            statement_page = generate_statement_page(financial_info, association)
            writer.add_page(statement_page)

        # Add uploaded extension PDF if available
        if 'extension_info' in financial_info and financial_info['extension_info'].get('form_7004_url'):
            extension_path = os.path.join(settings.MEDIA_ROOT, financial_info['extension_info']['form_7004_url'])
            if os.path.exists(extension_path):
                extension_reader = PdfReader(extension_path)
                for page in extension_reader.pages:
                    writer.add_page(page)
                logger.info(f"Extension PDF added from {extension_path}")
            elif settings.USE_AZURE_STORAGE and default_storage.exists(financial_info['extension_info']['form_7004_url']):
                # Try to get the extension from Azure Storage
                try:
                    azure_extension_content = default_storage.open(financial_info['extension_info']['form_7004_url']).read()
                    extension_reader = PdfReader(BytesIO(azure_extension_content))
                    for page in extension_reader.pages:
                        writer.add_page(page)
                    logger.info(f"Extension PDF added from Azure Storage")
                except Exception as e:
                    logger.warning(f"Could not add extension PDF from Azure Storage: {str(e)}")
            else:
                logger.warning(f"Extension PDF file not found at {extension_path}")

        # Append state return pages if applicable
        try:
            filing_state = association.get_filing_state()
            if filing_state == 'IL':
                # Add title page to separate state return from federal
                title_page = generate_state_title_page(association, tax_year)
                writer.add_page(title_page)

                il_pages = generate_il1120_pages(financial_info, association, preparer, tax_year=tax_year)
                for il_page in il_pages:
                    writer.add_page(il_page)
                logger.info(f"IL-1120 pages ({len(il_pages)}) appended for {association.association_name}")

                # Attach a copy of the federal 1120-H (required by IL instructions)
                try:
                    reader_copy = PdfReader(template_path)
                    page_copy = reader_copy.pages[0]
                    overlay_copy = PdfReader(BytesIO(overlay_bytes))
                    page_copy.merge_page(overlay_copy.pages[0])
                    writer.add_page(page_copy)
                    logger.info("1120-H copy attached for IL-1120 filing requirement")
                except Exception as e:
                    logger.error(f"Error attaching 1120-H copy for IL: {str(e)}", exc_info=True)

                # Append IL-1120-V payment voucher if amount owed > 0
                if il_amount_owed > 0:
                    try:
                        voucher_page = generate_il1120v_page(financial_info, association, tax_year=tax_year)
                        writer.add_page(voucher_page)
                        logger.info(f"IL-1120-V voucher appended (amount: ${il_amount_owed})")
                    except Exception as e:
                        logger.error(f"Error generating IL-1120-V voucher: {str(e)}", exc_info=True)
        except Exception as e:
            logger.error(f"Error generating IL-1120 pages: {str(e)}", exc_info=True)
            # Continue without IL pages - don't fail the federal return

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        logger.info(f"PDF generated successfully at {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        raise

def generate_state_title_page(association, tax_year):
    """Generate a title/separator page before the state return section."""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    page_width = letter[0]

    # Draw a horizontal rule
    y = 500
    can.setStrokeColorRGB(0.3, 0.3, 0.3)
    can.setLineWidth(2)
    can.line(100, y + 60, page_width - 100, y + 60)

    # State return title
    can.setFont("Helvetica-Bold", 24)
    state_name = dict(Association.STATE_CHOICES).get(association.get_filing_state(), association.get_filing_state())
    can.drawCentredString(page_width / 2, y, f"State of {state_name}")

    y -= 35
    can.setFont("Helvetica-Bold", 20)
    can.drawCentredString(page_width / 2, y, f"Tax Year {tax_year}")

    y -= 50
    can.setFont("Helvetica", 14)
    can.drawCentredString(page_width / 2, y, association.association_name)

    y -= 30
    can.drawCentredString(page_width / 2, y, f"EIN: {association.ein}")

    # Bottom rule
    y -= 40
    can.line(100, y, page_width - 100, y)

    # Note
    y -= 40
    can.setFont("Helvetica", 11)
    can.drawCentredString(page_width / 2, y, "The following pages contain the state tax return and supporting documents.")
    y -= 18
    can.drawCentredString(page_width / 2, y, "Mail the state return separately from the federal return.")

    can.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]


def generate_statement_page(financial_info, association):
    """Generate a statement page for additional income and deductions."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    # Add title
    elements.append(Paragraph("Federal Statements", title_style))
    elements.append(Paragraph(f"Association: {association.association_name}", normal_style))
    elements.append(Paragraph(f"EIN: {association.ein}", normal_style))
    elements.append(Paragraph(f"Year Ended: December 31, {financial_info.get('tax_year', '')}", normal_style))
    elements.append(Spacer(1, 12))

    # Other Income details
    if financial_info.get('total_other_income', 0) > 0:
        elements.append(Paragraph("Statement - Form 1120-H, Line 7 - OTHER INCOME", subtitle_style))
        other_income_data = [['Description', 'Amount']]
        other_income_data.extend([
            [item['description'], f"${item['amount']:,}"]
            for item in financial_info.get('additional_income', [])
        ])
        other_income_data.append(['Total Other Income', f"${financial_info['total_other_income']:,}"])
        
        other_income_table = Table(other_income_data, colWidths=[350, 100])
        other_income_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
                    ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
        
            # Bold "Total Other Deductions" row
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                
        ]))
        elements.append(other_income_table)
        elements.append(Spacer(1, 12))

    # Other Deductions details
    if financial_info.get('other_deductions', 0) > 0:
        elements.append(Paragraph("Statement - Form 1120-H, Line 15 - OTHER DEDUCTIONS", subtitle_style))
        other_deductions_data = [['Description', 'Amount']]
        other_deductions_data.extend([
            [item['description'], f"${item['amount']:,}"]
            for item in financial_info.get('other_deductions_detail', [])
            if item['amount'] > 0
        ])
        other_deductions_data.append(['Total Other Deductions', f"${financial_info['other_deductions']:,}"])
        
        other_deductions_table = Table(other_deductions_data, colWidths=[350, 100])
        other_deductions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
                        # Bold "Total Other Deductions" row
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        ]))
        elements.append(other_deductions_table)

    # Build the PDF
    doc.build(elements)
    
    # Create a new PDF page from the buffer
    statement_pdf = PdfReader(BytesIO(buffer.getvalue()))
    return statement_pdf.pages[0]

def generate_extension_page(extension_info, association):
    """Generate an extension page."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    # Add title
    elements.append(Paragraph("Extension Information", title_style))
    elements.append(Paragraph(f"Association: {association.association_name}", normal_style))
    elements.append(Paragraph(f"EIN: {association.ein}", normal_style))
    elements.append(Paragraph(f"Tax Year: {extension_info['tax_year']}", normal_style))
    elements.append(Spacer(1, 12))

    # Extension details
    elements.append(Paragraph("Form 7004 - Application for Automatic Extension of Time", subtitle_style))
    extension_data = [
        ['Filed Date', extension_info['filed_date'].strftime('%m/%d/%Y') if extension_info['filed_date'] else 'N/A'],
        ['Form 7004', 'Uploaded' if extension_info['form_7004_url'] else 'Not Uploaded'],
    ]
    
    extension_table = Table(extension_data, colWidths=[250, 200])
    extension_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(extension_table)

    # Build the PDF
    doc.build(elements)
    
    # Create a new PDF page from the buffer
    extension_pdf = PdfReader(BytesIO(buffer.getvalue()))
    return extension_pdf.pages[0]