import logging
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, IndirectObject
from datetime import date
import io
import os
from django.http import HttpResponse
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)

def generate_pdf(financial_info, association, preparer, tax_year):
    """Generate Form 1120-H PDF."""
    template_name = f'template_1120h_{tax_year}.pdf'
    template_path = settings.PDF_TEMPLATE_DIR / template_name
    output_path = settings.PDF_TEMP_DIR / f'form_1120h_{association.id}_{tax_year}.pdf'
    
    logger.info(f"Using template: {template_path}")
    
    # Make sure temp directory exists
    os.makedirs(settings.PDF_TEMP_DIR, exist_ok=True)
    
    try:
        generate_1120h_pdf(financial_info, association, preparer, str(template_path), str(output_path))
        
        with open(output_path, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=form_1120h_{association.id}_{tax_year}.pdf'
        
        os.remove(output_path)
        return response
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise

def fill_pdf_form(template_path, output_path, data):
    """Fill PDF form with data."""
    reader = PdfReader(template_path)
    writer = PdfWriter()
    page = reader.pages[0]
    writer.add_page(page)
    writer.update_page_form_field_values(writer.pages[0], {k: v for k, v in data.items() if v is not None})
    
    with open(output_path, "wb") as output_file:
        writer.write(output_file)

def checkbox_value(is_checked):
    """Convert boolean to PDF checkbox value."""
    return NameObject("/Yes") if is_checked else NameObject("/Off")

def format_number(value):
    """Format number with commas."""
    if value is None or value == '':
        return ''
    try:
        return f"{int(float(value)):,}"
    except ValueError:
        return str(value)

def generate_1120h_pdf(financial_info, association, preparer, template_path, output_path):
    """Generate 1120-H PDF with provided data."""
    data = {
        "f1_1": association.association_name,
        "f1_2": association.ein,
        "f1_3": association.mailing_address,
        "f1_4": f"{association.city}, {association.state} {association.zipcode}",
        "f1_5": association.formation_date.strftime("%m/%d/%Y"),
        
        "name_change": checkbox_value(financial_info.get('name_change', False)),
        "address_change": checkbox_value(financial_info.get('address_change', False)),
        "condo": checkbox_value(financial_info.get('condo', False)),
        "homeowners": checkbox_value(financial_info.get('homeowners', False)),
        
        "f1_6": format_number(financial_info.get('total_exempt_income')),
        "f1_7": format_number(financial_info.get('expenses_lineC')),
        "f1_8": format_number(financial_info.get('total_expenses')),
        "f1_9": format_number(financial_info.get('dividend_income')),
        "f1_10": format_number(financial_info.get('interest_income')),
        "f1_11": format_number(financial_info.get('rental_income')),
        "f1_15": format_number(financial_info.get('total_other_income')),
        "f1_16": format_number(financial_info.get('gross_income')),
        "f1_23": format_number(financial_info.get('other_deductions')),
        "f1_24": format_number(financial_info.get('total_deductions')),
        "f1_25": format_number(financial_info.get('taxable_income_before_100')),
        "f1_27": format_number(financial_info.get('taxable_income')),
        "f1_28": format_number(financial_info.get('total_tax')),
        "f1_30": format_number(financial_info.get('total_tax')),
        "f1_31": format_number(financial_info.get('estimated_payments')),
        "f1_32": format_number(financial_info.get('extension_payment')),
        "f1_35": format_number(financial_info.get('total_payments')),
        "f1_36": format_number(financial_info.get('amount_owed')),
        "f1_37": format_number(financial_info.get('overpayment')),
        "f1_38": format_number(financial_info.get('refunded')),
        
        "f1_39": preparer.name if preparer else '',
        "f1_40": preparer.ptin if preparer else '',
        "f1_41": preparer.firm_name if preparer else '',
        "f1_42": preparer.firm_ein if preparer else '',
        "f1_43": preparer.firm_address if preparer else '',
        "f1_44": preparer.firm_phone if preparer else '',
        "f1_45": date.today().strftime("%m/%d/%Y"),
        "f1_46": preparer.signature if preparer else '',
    }
    
    fill_pdf_form(template_path, output_path, data)