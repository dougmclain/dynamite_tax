import os
import logging
from pathlib import Path
from datetime import date
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
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

logger = logging.getLogger(__name__)

__all__ = ['generate_pdf']

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
    
    # Generate output path using the same directory as the template
    output_dir = template_path.parent.parent / 'temp_pdfs'
    output_path = output_dir / f'form_1120h_{association.id}_{tax_year}.pdf'
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Using output path: {output_path}")

    try:
        generate_1120h_pdf(financial_info, association, preparer, str(template_path), str(output_path))
        
        with open(output_path, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=form_1120h_{association.id}_{tax_year}.pdf'
        
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
        logger.error(f"Error in PDF generation: {str(e)}")
        raise

logger = logging.getLogger(__name__)

def to_pdf_object(value):
    if isinstance(value, bool):
        return BooleanObject(value)
    elif isinstance(value, int):
        return NumberObject(value)
    elif isinstance(value, float):
        return NumberObject(value)
    elif isinstance(value, str):
        return TextStringObject(value)
    else:
        return TextStringObject(str(value))

def inspect_pdf_template(template_path):
    reader = PdfReader(template_path)
    logger.info(f"Inspecting PDF template: {template_path}")
    logger.info(f"Number of pages: {len(reader.pages)}")
    
    for field_name, field in reader.get_fields().items():
        rect = field.get('/Rect')
        field_type = field.get('/FT')
        logger.info(f"Field: {field_name}, Type: {field_type}, Rect: {rect}")


FIELD_POSITIONS = {
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
}





NUMERIC_COLUMN_WIDTH = 80  # width in points

def format_number(value):
    """Format number without decimals and with commas for thousands."""
    return f"{int(value):,}"

def right_justify_text(can, text, x, y, width):
    text_width = pdfmetrics.stringWidth(text, 'Courier', 10)
    adjusted_x = x + width - text_width
    can.drawString(adjusted_x, y, text)


def generate_1120h_pdf(financial_info, association, preparer, template_path, output_path):
    """Generate PDF and return HTTP response."""
    try:
        reader = PdfReader(template_path)
        writer = PdfWriter()
        
        # Generate and add instructions page
        instructions_generator = InstructionsGenerator()
        instructions_page = instructions_generator.generate_page(
            financial_info,
            association,
            amount_owed=financial_info.get('amount_owed', 0),
            refund_amount=financial_info.get('refunded', 0)
        )
        writer.add_page(instructions_page)
        
        # Add the form page
        page = reader.pages[0]
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        data = prepare_pdf_data(financial_info, association, preparer)
        for key, value in data.items():
            if key in FIELD_POSITIONS:
                x, y = FIELD_POSITIONS[key]
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
        new_pdf = PdfReader(packet)
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
            else:
                logger.warning(f"Extension PDF file not found at {extension_path}")

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        logger.info(f"PDF generated successfully at {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        raise

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