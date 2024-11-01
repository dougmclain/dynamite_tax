import os
import logging
from datetime import date
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics

logger = logging.getLogger(__name__)

def format_number(value):
    """Format number without decimals and with commas for thousands."""
    if value is None or value == '':
        return ''
    try:
        return f"{int(float(value)):,}"
    except ValueError:
        logger.warning(f"Unable to format number: {value}")
        return str(value)
    
def format_tax_year(year):
    """Format tax year to show only last two digits."""
    return str(year)[-2:]

def generate_7004_extension(data, template_path, output_path):
    """Generate Form 7004 extension PDF.
    
    Args:
        data (dict): Dictionary containing all the form data
        template_path (str): Path to the Form 7004 template PDF
        output_path (str): Path where the completed PDF should be saved
    """
    try:
        # Verify template exists
        if not os.path.exists(template_path):
            logger.error(f"Template not found at: {template_path}")
            return False

        reader = PdfReader(template_path)
        writer = PdfWriter()
        page = reader.pages[0]

        # Create a new PDF with Reportlab to overlay the form fields
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        # Set default font
        can.setFont("Helvetica", 10)

        # Part I - Write Form Code (17 for Form 1120-H)
        can.drawString(555, 595, "1")  # Draw the "1"
        can.drawString(564, 595, "7")  # Draw the "7" slightly to the right

        # Write Association Information
        can.drawString(87, 682, data['association_name'])  # Name
        can.drawString(450, 682, data['ein'])  # EIN
        can.drawString(87, 658, data['address'])  # Address
        can.drawString(87, 635, f"{data['city']}, {data['state']} {data['zipcode']}")  # City, State, ZIP

        # Part II - Write Tax Year Information
        # Check box for calendar year
        can.drawString(217, 264, format_tax_year(data['tax_year']))  # Will display "23" for 2023

        # Function to right-align amounts in their boxes
        def draw_amount(amount, x, y):
            text = f"${format_number(amount)}"
            text_width = can.stringWidth(text, "Helvetica", 10)
            can.drawString(x - text_width, y, text)

        # Write Financial Information
        draw_amount(data['tentative_tax'], 550, 217)  # Line 6 - Tentative total tax
        draw_amount(data['total_payments'], 550, 194)  # Line 7 - Total payments and credits

        # Calculate and write balance due
        balance_due = max(0, data['tentative_tax'] - data['total_payments'])
        draw_amount(balance_due, 550, 171)  # Line 8 - Balance due

        # Save the form
        can.save()

        # Merge the new content with the template
        packet.seek(0)
        new_pdf = PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        
        writer.add_page(page)
        
        # Write the final PDF to file
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
            
        logger.info(f"Successfully generated Form 7004 PDF at: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error generating Form 7004 PDF: {str(e)}", exc_info=True)
        return False

def generate_extension_response(data, template_path):
    """Generate a Form 7004 PDF and return it as an HTTP response.
    
    Args:
        data (dict): Dictionary containing all the form data
        template_path (str): Path to the Form 7004 template PDF
    
    Returns:
        HttpResponse: Response containing the generated PDF
    """
    try:
        # Create temporary file path
        output_filename = f"form_7004_{data['ein']}_{data['tax_year']}.pdf"
        output_path = os.path.join(settings.PDF_TEMP_DIR, output_filename)

        # Generate the PDF
        success = generate_7004_extension(data, template_path, output_path)

        if success:
            # Read the generated PDF and create response
            with open(output_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{output_filename}"'

            # Clean up temporary file
            os.remove(output_path)
            
            return response
        else:
            logger.error("Failed to generate Form 7004 PDF")
            return None

    except Exception as e:
        logger.error(f"Error creating Form 7004 response: {str(e)}", exc_info=True)
        return None