import logging
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, IndirectObject
from datetime import date
import io

logger = logging.getLogger(__name__)

def fill_pdf_form(template_path, output_path, data):
    reader = PdfReader(template_path)
    writer = PdfWriter()

    # Get the first page
    page = reader.pages[0]
    writer.add_page(page)

    # Update form fields
    update_dict = {}
    for key, value in data.items():
        if value is not None:
            update_dict[key] = value

    writer.update_page_form_field_values(writer.pages[0], update_dict)

    # Write the output to a file
    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    # After writing, let's try to read the PDF and log the actual values
    reader = PdfReader(output_path)
    if reader.pages[0].get("/Annots"):
        for annot in reader.pages[0]["/Annots"]:
            if isinstance(annot, IndirectObject):
                annot = annot.get_object()
            if annot.get("/T"):
                field_name = annot["/T"]
                if field_name in ["name_change", "address_change", "condo", "homeowners"]:
                    field_value = annot.get("/V", "")
                    logger.debug(f"After writing - Field {field_name}: {field_value}")

def format_number(value):
    if value is None or value == '':
        return ''
    try:
        # Convert to float, then to integer to remove decimals, then format with commas
        return f"{int(float(value)):,}"
    except ValueError:
        logger.warning(f"Unable to format number: {value}")
        return str(value)
    
def checkbox_value(is_checked):
    return NameObject("/Yes") if is_checked else NameObject("/Off")


def generate_1120h_pdf(financial_info, association, preparer, template_path, output_path):
    data = {
        "f1_1": association.association_name,
        "f1_2": association.ein,
        "f1_3": association.mailing_address,
        "f1_4": f"{association.city}, {association.state} {association.zipcode}",
        "f1_5": association.formation_date.strftime("%m/%d/%Y"),
        
        # Checkboxes - use "On" instead of "Yes"
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
        
        # Preparer information
        "f1_39": preparer.name if preparer else '',
        "f1_40": preparer.ptin if preparer else '',
        "f1_41": preparer.firm_name if preparer else '',
        "f1_42": preparer.firm_ein if preparer else '',
        "f1_43": preparer.firm_address if preparer else '',
        "f1_44": preparer.firm_phone if preparer else '',
        "f1_45": date.today().strftime("%m/%d/%Y"),  # Preparer sign date
        "f1_46": preparer.signature if preparer else '',  # Preparer signature
    }

    logger.debug(f"PDF data being sent: {data}")
    logger.debug("Checkbox values:")
    logger.debug(f"name_change: '{data['name_change']}'")
    logger.debug(f"address_change: '{data['address_change']}'")
    logger.debug(f"condo: '{data['condo']}'")
    logger.debug(f"homeowners: '{data['homeowners']}'")

    for key, value in data.items():
        logger.debug(f"Field {key}: {value}")

    fill_pdf_form(template_path, output_path, data)