from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.utils import timezone
from ..models import Association, EngagementLetter
from ..forms import EngagementLetterForm
from django.template.loader import get_template
from datetime import datetime
import os
from io import BytesIO
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import logging

logger = logging.getLogger(__name__)

# Helper function for creating standardized filenames
def create_engagement_letter_filename(association, tax_year, signed=False):
    """Create a standardized filename for engagement letters."""
    # Create a safe name from the association name
    safe_name = ''.join(c for c in association.association_name if c.isalnum() or c.isspace())
    safe_name = safe_name.replace(' ', '_')
    if len(safe_name) > 30:
        safe_name = safe_name[:30]
    
    # Add 'signed_' prefix if this is a signed version
    prefix = 'signed_' if signed else ''
    
    # Return the formatted filename
    return f"{safe_name}_{prefix}eng_letter_{tax_year}.pdf"

class EngagementLetterView(LoginRequiredMixin, View):
    template_name = 'tax_form/engagement_letter.html'
    
    def get(self, request):
        current_year = timezone.now().year
        default_tax_year = current_year - 1
        form = EngagementLetterForm(initial={'tax_year': default_tax_year})
        engagement_letters = EngagementLetter.objects.all().order_by('-tax_year', 'association__association_name')
        
        context = {
            'form': form,
            'engagement_letters': engagement_letters,
            'today': timezone.now().date(),
        }
        return render(request, self.template_name, context)

    
    def post(self, request):
        form = EngagementLetterForm(request.POST)
        if form.is_valid():
            # Check if engagement letter already exists for this association and year
            association = form.cleaned_data['association']
            tax_year = form.cleaned_data['tax_year']
            
            engagement_letter, created = EngagementLetter.objects.get_or_create(
                association=association,
                tax_year=tax_year,
                defaults={'price': form.cleaned_data['price']}
            )
            
            if not created:
                engagement_letter.price = form.cleaned_data['price']
                engagement_letter.save()
            
            try:
                # Generate PDF
                pdf_response = self.generate_pdf(engagement_letter)
                
                # Display success message
                messages.success(request, f'Engagement letter for {association.association_name} - {tax_year} created successfully.')
                
                # Return the PDF directly
                pdf_filename = create_engagement_letter_filename(association, tax_year)
                response = HttpResponse(pdf_response.content, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={pdf_filename}'
                return response
            except Exception as e:
                logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
                messages.error(request, f"Error generating PDF: {str(e)}")
            
            return redirect('engagement_letter')
        
        engagement_letters = EngagementLetter.objects.all().order_by('-tax_year', 'association__association_name')
        context = {
            'form': form,
            'engagement_letters': engagement_letters,
            'today': timezone.now().date(),
        }
        return render(request, self.template_name, context)
    
    def generate_pdf(self, engagement_letter):
        """Generate a PDF engagement letter with improved formatting"""
        buffer = BytesIO()
        # Use a smaller margin to fit everything on one page
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
        
        # Get styles
        styles = getSampleStyleSheet()
        elements = []
        
        # Create a table for the header with logo and company info
        header_data = []
        
        # Try to add logo
        logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'dynamite_logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path)
            logo.drawHeight = 0.8*inch
            logo.drawWidth = 2*inch
            
            # Company header - right aligned
            company_header = Paragraph("""
            <para align="right">
            <b>Dynamite Management, LLC</b><br/>
            PO Box 8, Vancouver, WA 98666<br/>
            Phone: 360-524-9665<br/>
            Email: info@hoafiscal.com
            </para>""", styles['Normal'])
            
            # Add logo (left) and contact info (right) in a table
            header_data = [[logo, company_header]]
            header_table = Table(header_data, colWidths=[3*inch, 3*inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('LEFTPADDING', (0, 0), (0, 0), 0),
                ('RIGHTPADDING', (1, 0), (1, 0), 0),
            ]))
            elements.append(header_table)
        else:
            # Fallback to just text if logo not found
            company_header = Paragraph("""
            <para align="right">
            <b>Dynamite Management, LLC</b><br/>
            PO Box 8, Vancouver, WA 98666<br/>
            Phone: 360-524-9665<br/>
            Email: info@hoafiscal.com
            </para>""", styles['Normal'])
            elements.append(company_header)
        
        # Add some space after the header
        elements.append(Spacer(1, 0.5*inch))
        
        # Introduction - style the association name in bold
        intro = f"""We are pleased to confirm our understanding of the services we are to provide for:
        <b>{engagement_letter.association.association_name}</b>, for the year ended December 31, {engagement_letter.tax_year}. 
        This letter sets forth the terms of our engagement."""
        elements.append(Paragraph(intro, styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))
        
        # Services section
        services = """<b>Services Provided:</b><br/>
        Dynamite Management, LLC will prepare the federal Form 1120H for the tax year ending December 31,
        2024. Our services will include the preparation of the tax forms based on the financial information
        provided by you. It is your responsibility to provide all the necessary information required for the
        preparation of complete and accurate returns."""
        elements.append(Paragraph(services, styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))
        
        # Fees section - make the price bold and a bit larger
        fees = f"""<b>Fees:</b><br/>
        The fee for the preparation of the Form 1120H will be: <b>${engagement_letter.price}</b><br/>
        These fees are based on the assumption that all information provided by you is accurate and
        complete and that you will provide all required information in a timely manner. Any additional
        services or consultations beyond the scope of this engagement will be billed separately."""
        elements.append(Paragraph(fees, styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))
        
        # Responsibilities section - reduce text to fit on one page
        responsibilities = """<b>Responsibilities:</b><br/>
        It is your responsibility to provide all the information required for the preparation of the tax returns.
        You are also responsible for reviewing the returns for accuracy and completeness before they are
        filed. You are responsible for the payment of all taxes due. You should retain all the documents and
        other data that form the basis of this return for at least seven (7) years.
        
        By signing below, you are also taking responsibility for making all management decisions and
        performing all management functions; for designating an individual with suitable skill, knowledge, or
        experience to oversee the tax services provided."""
        elements.append(Paragraph(responsibilities, styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))
        
        # Consent section
        consent = """<b>Consent to Use of Tax Return Information:</b><br/>
        You acknowledge and agree that Dynamite Management, LLC may use your association's tax return
        information provided for the purpose of preparing your tax returns."""
        elements.append(Paragraph(consent, styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))
        
        # Signature section with more space
        signature = """To indicate your agreement to the arrangements above, please sign and date this letter.
        """
        elements.append(Paragraph(signature, styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Create a table for signature, title, and date lines with more space
        sig_data = [
            ["Signature:_________________________", "Date:_________________"],
            ["Title:_____________________________", ""]
        ]
        sig_table = Table(sig_data, colWidths=[4*inch, 2*inch])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(sig_table)
        
        # Build the PDF
        doc.build(elements)
        
        # Create a response with the formatted filename
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type='application/pdf')
        response.write(pdf)
        
        # Use consistent filename format
        pdf_filename = create_engagement_letter_filename(engagement_letter.association, engagement_letter.tax_year)
        response['Content-Disposition'] = f'inline; filename={pdf_filename}'
        
        return response

class DownloadEngagementLetterView(LoginRequiredMixin, View):
    """View to download an engagement letter PDF"""
    
    def get(self, request, letter_id):
        engagement_letter = get_object_or_404(EngagementLetter, id=letter_id)
        
        # Generate PDF
        pdf_response = EngagementLetterView().generate_pdf(engagement_letter)
        
        # Return PDF directly as a response
        pdf_filename = create_engagement_letter_filename(engagement_letter.association, engagement_letter.tax_year)
        response = HttpResponse(pdf_response.content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
        
        return response

class DeleteEngagementLetterView(LoginRequiredMixin, View):
    """View to delete an engagement letter"""
    
    def post(self, request, letter_id):
        engagement_letter = get_object_or_404(EngagementLetter, id=letter_id)
        association_name = engagement_letter.association.association_name
        tax_year = engagement_letter.tax_year
        
        # Delete the PDF files if they exist
        if engagement_letter.pdf_file:
            try:
                if os.path.exists(engagement_letter.pdf_file.path):
                    os.remove(engagement_letter.pdf_file.path)
            except:
                logger.warning(f"Could not delete file: {engagement_letter.pdf_file.path}")
        
        if engagement_letter.signed_pdf:
            try:
                if os.path.exists(engagement_letter.signed_pdf.path):
                    os.remove(engagement_letter.signed_pdf.path)
            except:
                logger.warning(f"Could not delete file: {engagement_letter.signed_pdf.path}")
        
        # Delete the database record
        engagement_letter.delete()
        
        messages.success(request, f'Engagement letter for {association_name} - {tax_year} deleted successfully.')
        return redirect('engagement_letter')

class UploadSignedEngagementLetterFormView(LoginRequiredMixin, View):
    """View to show the form for uploading a signed engagement letter"""
    template_name = 'tax_form/upload_signed_engagement_letter.html'
    
    def get(self, request, letter_id):
        engagement_letter = get_object_or_404(EngagementLetter, id=letter_id)
        context = {
            'letter': engagement_letter,
            'today': timezone.now().date()
        }
        return render(request, self.template_name, context)

class UploadSignedEngagementLetterView(LoginRequiredMixin, View):
    """View to handle the upload of a signed engagement letter"""
    
    def post(self, request, letter_id):
        engagement_letter = get_object_or_404(EngagementLetter, id=letter_id)
        
        # Debug information
        logger.debug(f"Received upload request for letter ID: {letter_id}")
        logger.debug(f"Files in request: {list(request.FILES.keys())}")
        logger.debug(f"POST data keys: {list(request.POST.keys())}")
        
        if 'signed_pdf' in request.FILES:
            # Get form data
            signed_pdf = request.FILES['signed_pdf']
            signed_by = request.POST.get('signed_by', '')
            signer_title = request.POST.get('signer_title', '')
            date_signed = request.POST.get('date_signed')
            
            logger.debug(f"Uploaded file: {signed_pdf.name}, size: {signed_pdf.size}")
            
            try:
                # Update the engagement letter
                engagement_letter.signed_by = signed_by
                engagement_letter.signer_title = signer_title
                
                if date_signed:
                    engagement_letter.date_signed = date_signed
                
                # Get file data to memory
                pdf_data = signed_pdf.read()
                
                # Update status
                engagement_letter.status = 'signed'
                engagement_letter.save()
                
                messages.success(request, f'Signed engagement letter for {engagement_letter.association.association_name} uploaded successfully.')
                
                # Return the uploaded PDF
                pdf_filename = create_engagement_letter_filename(engagement_letter.association, engagement_letter.tax_year, signed=True)
                response = HttpResponse(pdf_data, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                return response
            except Exception as e:
                logger.error(f"Error processing signed PDF: {str(e)}", exc_info=True)
                messages.error(request, f'Error processing signed PDF: {str(e)}')
        else:
            logger.warning("No file found in request.FILES")
            messages.error(request, 'No file was uploaded. Please select a PDF file.')
            
        return redirect('engagement_letter')

class MarkEngagementLetterSentView(LoginRequiredMixin, View):
    """View to mark an engagement letter as sent"""
    
    def get(self, request, letter_id):
        engagement_letter = get_object_or_404(EngagementLetter, id=letter_id)
        
        # Update status
        engagement_letter.status = 'sent'
        engagement_letter.save()
        
        messages.success(request, f'Engagement letter for {engagement_letter.association.association_name} marked as sent.')
        return redirect('engagement_letter')