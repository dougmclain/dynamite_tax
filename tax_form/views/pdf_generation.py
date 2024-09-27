import os
import logging
from datetime import date
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from ..models import Financial, Association, Preparer
from .helpers import format_number, get_statement_details, prepare_pdf_data

logger = logging.getLogger(__name__)

__all__ = ['generate_pdf']

def generate_pdf(financial_info, association, preparer, tax_year):
    """Generate PDF and return HTTP response."""
    template_path = os.path.join(settings.PDF_TEMPLATE_DIR, settings.PDF_TEMPLATE_NAME)
    temp_dir = settings.PDF_TEMP_DIR
    output_path = os.path.join(temp_dir, f'form_1120h_{association.id}_{tax_year}.pdf')

    logger.info(f"Attempting to access PDF template at: {template_path}")
    
    if not os.path.exists(template_path):
        logger.error(f"PDF template not found at {template_path}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"PDF_TEMPLATE_DIR contents: {os.listdir(settings.PDF_TEMPLATE_DIR)}")
        raise FileNotFoundError(f"PDF template not found at {template_path}")

    # Ensure the temporary directory exists
    try:
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Temporary directory ensured at: {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to create temporary directory: {str(e)}")
        raise

    try:
        generate_1120h_pdf(financial_info, association, preparer, template_path, output_path)
        
        with open(output_path, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=form_1120h_{association.id}_{tax_year}.pdf'
        
        os.remove(output_path)  # Clean up the temporary file
        logger.info(f"Temporary PDF file removed: {output_path}")
        
        return response
    except PermissionError:
        logger.error(f"Permission denied when writing to {output_path}")
        raise PermissionError(f"Permission denied when writing to {output_path}. Please check directory permissions.")
    except Exception as e:
        logger.error(f"Error in PDF generation: {str(e)}")
        raise

def generate_1120h_pdf(financial_info, association, preparer, template_path, output_path):
    """Generate the 1120-H PDF form."""
    data = prepare_pdf_data(financial_info, association, preparer)

    # Convert checkbox values to NameObject
    for key in ['name_change', 'address_change', 'condo', 'homeowners']:
        data[key] = NameObject("/Yes") if data[key] == "Yes" else NameObject("/Off")

    logger.debug(f"PDF data being sent: {data}")
    logger.debug("Checkbox values:")
    logger.debug(f"name_change: '{data['name_change']}'")
    logger.debug(f"address_change: '{data['address_change']}'")
    logger.debug(f"condo: '{data['condo']}'")
    logger.debug(f"homeowners: '{data['homeowners']}'")

    try:
        reader = PdfReader(template_path)
        writer = PdfWriter()
        page = reader.pages[0]
        writer.add_page(page)
        writer.update_page_form_field_values(writer.pages[0], data)
        
        # Check if we need to add a statement
        if financial_info.get('total_other_income', 0) > 0 or financial_info.get('other_deductions', 0) > 0:
            statement_page = generate_statement_page(financial_info, association)
            writer.add_page(statement_page)
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        logger.info(f"PDF generated successfully at {output_path}")
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
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
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
        ]))
        elements.append(other_income_table)
        elements.append(Spacer(1, 12))

    # Other Deductions details
    if financial_info.get('other_deductions', 0) > 0:
        elements.append(Paragraph("Statement - Form 1120-H, Line 15 - OTHER DEDUCTIONS", subtitle_style))
        other_deductions_data = [['Description', 'Amount']]
        other_deductions_data.extend([
            [item['description'], f"${item['amount']:,}"]
            for item in financial_info.get('additional_expenses', [])
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
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
        ]))
        elements.append(other_deductions_table)

    # Build the PDF
    doc.build(elements)
    
    # Create a new PDF page from the buffer
    statement_pdf = PdfReader(BytesIO(buffer.getvalue()))
    return statement_pdf.pages[0]