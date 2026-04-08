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

# Year-specific field positions for Form 7004
# The 2024 template has a page height of 783, while 2025 uses standard 792 (letter)
EXTENSION_POSITIONS_BY_YEAR = {
    2024: {
        'form_code': (555, 595),
        'name': (87, 682),
        'ein': (450, 682),
        'address': (87, 658),
        'city_state_zip': (87, 635),
        'tax_year': (217, 264),
        'line_6': (550, 217),
        'line_7': (550, 194),
        'line_8': (550, 171),
    },
    2025: {
        'form_code': (549, 602),
        'name': (90, 688),
        'ein': (449, 688),
        'address': (90, 664),
        'city': (90, 640),
        'state': (277, 640),
        'zip': (492, 640),
        'tax_year': (225, 268),
        'line_6': (573, 220),
        'line_7': (573, 196),
        'line_8': (573, 172),
    },
}

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

        # Remove form field widget annotations from the template page —
        # their white backgrounds obscure any text we overlay
        if '/Annots' in page:
            from PyPDF2.generic import ArrayObject, NameObject
            annots = page['/Annots']
            resolved = annots.get_object() if hasattr(annots, 'get_object') else annots
            cleaned = ArrayObject([
                a for a in resolved
                if a.get_object().get('/Subtype') != '/Widget'
            ])
            page[NameObject('/Annots')] = cleaned

        # Create a new PDF with Reportlab to overlay the form fields
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        # Set default font - use bold so text isn't obscured by template field backgrounds
        can.setFont("Helvetica-Bold", 10)
        can.setFillColor(colors.black)

        # Get year-specific field positions (default to 2024 for older years)
        tax_year = int(data.get('tax_year', 2024))
        pos = EXTENSION_POSITIONS_BY_YEAR.get(tax_year, EXTENSION_POSITIONS_BY_YEAR[2024])

        # Part I - Write Form Code (17 for Form 1120-H)
        fc_x, fc_y = pos['form_code']
        can.drawString(fc_x, fc_y, "1")  # Draw the "1"
        can.drawString(fc_x + 9, fc_y, "7")  # Draw the "7" slightly to the right

        # Write Association Information
        name_x, name_y = pos['name']
        can.drawString(name_x, name_y, data['association_name'])  # Name
        ein_x, ein_y = pos['ein']
        can.drawString(ein_x, ein_y, data['ein'])  # EIN
        addr_x, addr_y = pos['address']
        can.drawString(addr_x, addr_y, data['address'])  # Address

        # 2025+ forms have separate City, State, ZIP boxes
        if 'city' in pos:
            city_x, city_y = pos['city']
            can.drawString(city_x, city_y, data['city'])
            state_x, state_y = pos['state']
            can.drawString(state_x, state_y, data['state'])
            zip_x, zip_y = pos['zip']
            can.drawString(zip_x, zip_y, data['zipcode'])
        else:
            csz_x, csz_y = pos['city_state_zip']
            can.drawString(csz_x, csz_y, f"{data['city']}, {data['state']} {data['zipcode']}")

        # Part II - Write Tax Year Information
        ty_x, ty_y = pos['tax_year']
        can.drawString(ty_x, ty_y, format_tax_year(data['tax_year']))

        # Function to right-align amounts in their boxes
        def draw_amount(amount, x, y):
            text = f"${format_number(amount)}"
            text_width = can.stringWidth(text, "Helvetica-Bold", 10)
            can.drawString(x - text_width, y, text)

        # Write Financial Information
        l6_x, l6_y = pos['line_6']
        draw_amount(data['tentative_tax'], l6_x, l6_y)  # Line 6 - Tentative total tax
        l7_x, l7_y = pos['line_7']
        draw_amount(data['total_payments'], l7_x, l7_y)  # Line 7 - Total payments and credits

        # Calculate and write balance due
        balance_due = max(0, data['tentative_tax'] - data['total_payments'])
        l8_x, l8_y = pos['line_8']
        draw_amount(balance_due, l8_x, l8_y)  # Line 8 - Balance due

        # Save the form
        can.save()

        # Merge our text ON TOP of the template so form field
        # backgrounds don't obscure the filled-in values
        packet.seek(0)
        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])

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