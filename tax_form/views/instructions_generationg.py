"""Module for generating instruction pages for tax returns."""

import logging
import os
import traceback
from datetime import date
from io import BytesIO
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader
from .helpers import format_number

logger = logging.getLogger(__name__)

class InstructionsGenerator:
    """Class to handle generation of instruction pages."""
    
    KANSAS_CITY_STATES = {
        'CT', 'DE', 'DC', 'GA', 'IL', 'IN', 'KY', 'ME', 'MD', 'MA', 'MI', 
        'NH', 'NJ', 'NY', 'NC', 'OH', 'PA', 'RI', 'SC', 'TN', 'VT', 'VA', 
        'WV', 'WI'
    }
    
    OGDEN_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'FL', 'HI', 'ID', 'IA', 'KS',
        'LA', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NM', 'ND', 'OK', 'OR',
        'SD', 'TX', 'UT', 'WA', 'WY'
    }

    def __init__(self):
        """Initialize with logo paths."""
        # Define logo paths using full path
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        self.logo_paths = {
            'dynamite': os.path.join(static_dir, 'images', 'dynamite_logo.png'),
            'hoatax': os.path.join(static_dir, 'images', 'hoatax_logo.png')
        }
        logger.info(f"Logo paths initialized: {self.logo_paths}")

    @classmethod
    def get_filing_address(cls, state):
        """Determine the filing address based on state."""
        if state.upper() in cls.KANSAS_CITY_STATES:
            return ("Department of the Treasury\n"
                   "Internal Revenue Service Center\n"
                   "Kansas City, MO 64999-0012")
        elif state.upper() in cls.OGDEN_STATES:
            return ("Department of the Treasury\n"
                   "Internal Revenue Service Center\n"
                   "Ogden, UT 84201-0012")
        else:
            return ("Internal Revenue Service Center\n"
                   "P.O. Box 409101\n"
                   "Ogden, UT 84409")

    def draw_logos(self, canvas_obj):
        """Draw logos on the canvas if they exist."""
        try:
            # Logo dimensions and positioning
            dynamite_logo_height = 40
            hoatax_logo_height = 60  # Slightly larger
            margin_top = 730

            logger.info("Starting logo drawing process...")
            
            # Try to draw Dynamite logo on the left
            if os.path.exists(self.logo_paths['dynamite']):
                logger.info(f"Found Dynamite logo at: {self.logo_paths['dynamite']}")
                try:
                    img = ImageReader(self.logo_paths['dynamite'])
                    # Get image dimensions
                    img_width, img_height = img.getSize()
                    logger.info(f"Dynamite logo dimensions: {img_width}x{img_height}")
                    
                    # Calculate width while maintaining aspect ratio
                    aspect_ratio = img_width / img_height
                    new_width = dynamite_logo_height* aspect_ratio
                    
                    # Draw with explicit width and height
                    canvas_obj.drawImage(
                        img, 
                        168 - new_width,  # x position (page width - logo width - right margin)
                        margin_top,  # y
                        width=new_width,
                        height=dynamite_logo_height,
                        mask='auto'  # Handle transparency
                    )
                    logger.info(f"Drew Dynamite logo at position (50, {margin_top}) with size {new_width}x{dynamite_logo_height}")
                except Exception as e:
                    logger.error(f"Error drawing Dynamite logo: {str(e)}")
            else:
                logger.warning(f"Dynamite logo not found at {self.logo_paths['dynamite']}")

            # Try to draw HOA Tax logo on the right
            if os.path.exists(self.logo_paths['hoatax']):
                logger.info(f"Found HOA Tax logo at: {self.logo_paths['hoatax']}")
                try:
                    img = ImageReader(self.logo_paths['hoatax'])
                    # Get image dimensions
                    img_width, img_height = img.getSize()
                    logger.info(f"HOA Tax logo dimensions: {img_width}x{img_height}")
                    
                    # Calculate width while maintaining aspect ratio
                    aspect_ratio = img_width / img_height
                    new_width = hoatax_logo_height * aspect_ratio
                    
                    # Draw with explicit width and height
                    canvas_obj.drawImage(
                        img, 
                        510,  # x
                        margin_top,  # y
                        width=new_width,
                        height=hoatax_logo_height,
                        mask='auto'  # Handle transparency
                    )
                    logger.info(f"Drew HOA Tax logo at position (400, {margin_top}) with size {new_width}x{hoatax_logo_height}")
                except Exception as e:
                    logger.error(f"Error drawing HOA Tax logo: {str(e)}")
            else:
                logger.warning(f"HOA Tax logo not found at {self.logo_paths['hoatax']}")



        except Exception as e:
            logger.error(f"Error in draw_logos: {str(e)}\n{traceback.format_exc()}")
            # Continue without logos if there's an error

    @staticmethod
    def draw_wrapped_text(canvas_obj, text, x, y, width):
        """Draw text that automatically wraps within a specified width."""
        words = text.split()
        line = []
        for word in words:
            line.append(word)
            line_width = canvas_obj.stringWidth(' '.join(line), "Helvetica", 10)
            if line_width > width:
                line.pop()
                canvas_obj.drawString(x, y, ' '.join(line))
                y -= 15
                line = [word]
        if line:
            canvas_obj.drawString(x, y, ' '.join(line))
            y -= 15
        return y

    @staticmethod
    def draw_address_block(canvas_obj, label, address_lines, x, y):
        """Draw a prominent boxed address block with a label and address lines."""
        line_height = 16
        padding_top = 14
        padding_bottom = 10
        padding_side = 10
        box_height = padding_top + padding_bottom + line_height * (len(address_lines) + 1)
        box_width = 300

        # Draw light gray background box
        canvas_obj.setFillColorRGB(0.94, 0.94, 0.94)
        canvas_obj.setStrokeColorRGB(0.5, 0.5, 0.5)
        canvas_obj.roundRect(x, y - box_height + padding_top, box_width, box_height, 4, fill=1, stroke=1)
        canvas_obj.setFillColorRGB(0, 0, 0)

        # Draw label (with top padding inside box)
        inner_y = y - 2
        canvas_obj.setFont("Helvetica-Bold", 11)
        canvas_obj.drawString(x + padding_side, inner_y, label)
        inner_y -= line_height

        # Draw address lines
        canvas_obj.setFont("Helvetica-Bold", 12)
        for line in address_lines:
            canvas_obj.drawString(x + padding_side + 10, inner_y, line)
            inner_y -= line_height

        # Reset font
        canvas_obj.setFont("Helvetica", 10)
        return y - box_height - 10

    def generate_page(self, financial_info, association, amount_owed=0, refund_amount=0, il_amount_owed=0, il_refund=0):
        """Generate instructions page for the tax return."""
        try:
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            # Draw logos at the top
            self.draw_logos(can)
            
            # Start content below logos
            y = 690  # Adjusted starting position to account for logos
            
            # Current date
            current_date = date.today().strftime("%B %d, %Y")
            can.drawString(50, y, current_date)
            y -= 25

            # Instructions header
            can.setFont("Helvetica-Bold", 12)
            can.drawString(50, y, "Instructions for Filing Your Form 1120-H")
            y -= 25
            
            can.setFont("Helvetica", 10)
            
            # Review instructions with added text about keeping a copy
            review_text = ("Please review the form carefully to make sure there are no errors or "
                         "missing information. Make a complete copy of the signed return for your "
                         "records before mailing. We recommend that you mail the return to the Internal "
                         "Revenue Service certified, return receipt. Keep all records you used to "
                         "prepare the return for at least seven years.")
            y = self.draw_wrapped_text(can, review_text, 50, y, 500)
            y -= 15

            due_year = str(int(financial_info['tax_year']) + 1)

            # ========================================
            # FEDERAL RETURN SECTION
            # ========================================
            can.setFont("Helvetica-Bold", 12)
            can.drawString(50, y, "Federal Form 1120-H:")
            y -= 3
            can.setStrokeColorRGB(0, 0, 0)
            can.line(50, y, 550, y)
            y -= 15

            # Signature requirement
            can.setFont("Helvetica-Bold", 10)
            can.drawString(50, y, "Signature Required:")
            can.setFont("Helvetica", 10)
            y -= 15
            can.drawString(70, y, "The return must be signed and dated by an officer of the Association.")
            y -= 20

            # Federal balance due or refund
            can.setFont("Helvetica-Bold", 10)
            can.drawString(50, y, "Balance Due or Refund:")
            can.setFont("Helvetica", 10)
            y -= 15
            if amount_owed > 0:
                payment_text = (f"The Association has a federal balance due of ${format_number(amount_owed)}. "
                            "DO NOT SEND A CHECK WITH THIS RETURN. To pay your balance due, "
                            "login to the Electronic Federal Tax Payment System (EFTPS) at "
                            "www.eftps.gov or call 1-800-555-4477.")
                y = self.draw_wrapped_text(can, payment_text, 70, y, 480)
            elif refund_amount > 0:
                can.drawString(70, y, f"You should receive a federal refund of ${format_number(refund_amount)}.")
                y -= 15
            else:
                can.drawString(70, y, "There is $0 due with this federal return.")
                y -= 15
            y -= 5

            # Federal due date
            can.setFont("Helvetica-Bold", 10)
            can.drawString(50, y, "Date Due:")
            can.setFont("Helvetica", 10)
            y -= 15
            if financial_info.get('extension_info'):
                due_date = f"October 15, {due_year}"
            else:
                due_date = f"April 15, {due_year}"
            can.drawString(70, y, f"File your federal return on or before {due_date}.")
            y -= 20

            # Extension information if applicable
            if financial_info.get('extension_info'):
                can.setFont("Helvetica-Bold", 10)
                can.drawString(50, y, "Extension:")
                can.setFont("Helvetica", 10)
                y -= 15
                can.drawString(70, y, "Attach a copy of your extension before mailing the return.")
                y -= 20

            # Federal filing address
            address = self.get_filing_address(association.state)
            address_lines = address.split('\n')
            y = self.draw_address_block(can, "Mail Federal Return To:", address_lines, 70, y)

            # ========================================
            # STATE RETURN SECTION (if applicable)
            # ========================================
            if association.get_filing_state() == 'IL':
                y -= 10
                can.setFont("Helvetica-Bold", 12)
                can.drawString(50, y, "Illinois Form IL-1120:")
                y -= 3
                can.setStrokeColorRGB(0, 0, 0)
                can.line(50, y, 550, y)
                y -= 15

                state_text = ("An Illinois Form IL-1120 has been prepared and is included in this packet. "
                              "A copy of the federal Form 1120-H is attached to the IL-1120 as required by Illinois.")
                can.setFont("Helvetica", 10)
                y = self.draw_wrapped_text(can, state_text, 70, y, 480)
                y -= 5

                # IL signature requirement
                can.setFont("Helvetica-Bold", 10)
                can.drawString(50, y, "Signature Required:")
                can.setFont("Helvetica", 10)
                y -= 15
                can.drawString(70, y, "The IL-1120 must also be signed and dated by the paid preparer.")
                y -= 20

                # IL balance due or refund
                if il_amount_owed > 0:
                    can.setFont("Helvetica-Bold", 10)
                    can.drawString(50, y, "Illinois Balance Due:")
                    can.setFont("Helvetica", 10)
                    y -= 15
                    il_due_text = (f"Illinois balance due: ${format_number(il_amount_owed)}. "
                                  "An IL-1120-V payment voucher is included. Mail the IL-1120, the attached "
                                  "1120-H, and the voucher with your check or money order payable to "
                                  "\"Illinois Department of Revenue\". "
                                  "You may also pay electronically at mytax.illinois.gov.")
                    y = self.draw_wrapped_text(can, il_due_text, 70, y, 480)
                    y -= 5
                    il_address_lines = [
                        "Illinois Department of Revenue",
                        "PO BOX 19038",
                        "Springfield, IL 62794-9038",
                    ]
                    y = self.draw_address_block(can, "Mail Illinois Return To:", il_address_lines, 70, y)
                elif il_refund > 0:
                    can.setFont("Helvetica-Bold", 10)
                    can.drawString(50, y, "Illinois Refund:")
                    can.setFont("Helvetica", 10)
                    y -= 15
                    can.drawString(70, y, f"Illinois state refund: ${format_number(il_refund)}.")
                    y -= 15
                    y -= 5
                    il_address_lines = [
                        "Illinois Department of Revenue",
                        "PO BOX 19048",
                        "Springfield, IL 62794-9048",
                    ]
                    y = self.draw_address_block(can, "Mail Illinois Return To:", il_address_lines, 70, y)
                else:
                    can.setFont("Helvetica", 10)
                    can.drawString(70, y, "No Illinois state tax is due with this return.")
                    y -= 15
                    y -= 5
                    il_address_lines = [
                        "Illinois Department of Revenue",
                        "PO BOX 19048",
                        "Springfield, IL 62794-9048",
                    ]
                    y = self.draw_address_block(can, "Mail Illinois Return To:", il_address_lines, 70, y)

                # IL due date
                y -= 5
                can.setFont("Helvetica-Bold", 10)
                can.drawString(50, y, "Illinois Date Due:")
                can.setFont("Helvetica", 10)
                y -= 15
                il_due_year = str(int(financial_info['tax_year']) + 1)
                if financial_info.get('extension_info'):
                    il_due_text = f"File your Illinois return on or before November 15, {il_due_year} (automatic 7-month extension)."
                else:
                    il_due_text = f"File your Illinois return on or before April 15, {il_due_year}."
                y = self.draw_wrapped_text(can, il_due_text, 70, y, 480)
            else:
                y -= 10
                can.setFont("Helvetica-Bold", 10)
                can.drawString(50, y, "State Filing:")
                can.setFont("Helvetica", 10)
                y -= 15
                state_text = ("Your Association may be required to file a state tax return. "
                             "Please contact your state authority to determine the requirements.")
                y = self.draw_wrapped_text(can, state_text, 70, y, 480)
            y -= 25

            # Contact information
            contact_text = ("Thank you for using Dynamite Management to prepare your return. If you have "
                          "any questions, please don't hesitate to contact us at 360-524-9665 or "
                          "info@hoafiscal.com")
            y = self.draw_wrapped_text(can, contact_text, 50, y, 500)

            can.save()
            packet.seek(0)
            return PdfReader(packet).pages[0]

        except Exception as e:
            logger.error(f"Error generating page: {str(e)}\n{traceback.format_exc()}")
            raise