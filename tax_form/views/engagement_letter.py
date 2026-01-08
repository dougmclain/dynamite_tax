from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.utils import timezone
from ..models import Association, EngagementLetter, EngagementLetterTemplate, StateEngagementTemplate
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
from azure.storage.blob import BlobServiceClient

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

        # Get distinct tax years for filtering
        tax_years = EngagementLetter.objects.values_list('tax_year', flat=True).distinct().order_by('-tax_year')

        context = {
            'form': form,
            'engagement_letters': engagement_letters,
            'tax_years': tax_years,
            'today': timezone.now().date(),
        }
        return render(request, self.template_name, context)

    
    def post(self, request):
        form = EngagementLetterForm(request.POST)
        if form.is_valid():
            # Check if engagement letter already exists for this association and year
            association = form.cleaned_data['association']
            tax_year = form.cleaned_data['tax_year']
            price = form.cleaned_data['price']
            state_fee = form.cleaned_data.get('state_fee', 0) or 0
            override_filing_state = form.cleaned_data.get('override_filing_state', '')

            # If user specified a filing state, update the association
            if override_filing_state:
                association.filing_state = override_filing_state
                association.save()

            engagement_letter, created = EngagementLetter.objects.get_or_create(
                association=association,
                tax_year=tax_year,
                defaults={'price': price, 'state_fee': state_fee}
            )

            if not created:
                engagement_letter.price = price
                engagement_letter.state_fee = state_fee
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

class UploadSignedEngagementLetterView(LoginRequiredMixin, View):
    """View to handle both showing and processing the upload form"""
    template_name = 'tax_form/upload_signed_engagement_letter.html'
    
    def get(self, request, letter_id):
        """Display the upload form"""
        engagement_letter = get_object_or_404(EngagementLetter, id=letter_id)
        context = {
            'letter': engagement_letter,
            'today': timezone.now().date()
        }
        return render(request, self.template_name, context)
    
    def post(self, request, letter_id):
        """Process the upload form"""
        engagement_letter = get_object_or_404(EngagementLetter, id=letter_id)
        
        # Debug information
        logger.debug(f"Received upload request for letter ID: {letter_id}")
        logger.debug(f"Files in request: {list(request.FILES.keys())}")
        logger.debug(f"POST data keys: {list(request.POST.keys())}")
        
        if 'signed_pdf' in request.FILES:
            # Get form data (all are now optional)
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
                else:
                    engagement_letter.date_signed = timezone.now().date()
                
                # Create a custom filename for the PDF
                safe_name = ''.join(c for c in engagement_letter.association.association_name if c.isalnum() or c.isspace())
                safe_name = safe_name.replace(' ', '_')
                if len(safe_name) > 30:
                    safe_name = safe_name[:30]
                
                # Full path for the blob
                blob_path = f"signed_engagement_letters/{safe_name}_signed_eng_letter_{engagement_letter.tax_year}.pdf"
                
                # Read file content
                file_content = signed_pdf.read()
                
                # Connect to Azure directly
                connection_string = f"DefaultEndpointsProtocol=https;AccountName={settings.AZURE_ACCOUNT_NAME};AccountKey={settings.AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER)
                
                # Create content settings
                content_settings = None
                try:
                    from azure.storage.blob import ContentSettings
                    content_settings = ContentSettings(
                        content_type="application/pdf",
                        cache_control="public, max-age=86400"
                    )
                except ImportError:
                    logger.warning("ContentSettings import failed, uploading without content settings")
                
                # Upload directly to Azure
                blob_client = container_client.get_blob_client(blob_path)
                if content_settings:
                    blob_client.upload_blob(file_content, overwrite=True, content_settings=content_settings)
                else:
                    blob_client.upload_blob(file_content, overwrite=True)
                
                # Store the blob path in the model
                engagement_letter.signed_pdf = blob_path
                logger.info(f"Uploaded signed engagement letter to Azure: {blob_path}")
                
                # Get the direct URL
                full_url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER}/{blob_path}"
                logger.debug(f"Signed engagement letter URL: {full_url}")
                
                # Update status
                engagement_letter.status = 'signed'
                engagement_letter.save()
                
                messages.success(request, f'Signed engagement letter for {engagement_letter.association.association_name} uploaded successfully.')
                
                # Redirect back to engagement letters list
                return redirect('engagement_letter')
            except Exception as e:
                logger.error(f"Error processing signed PDF: {str(e)}", exc_info=True)
                messages.error(request, f'Error processing signed PDF: {str(e)}')
                
                # If there's an error, re-render the form
                context = {
                    'letter': engagement_letter,
                    'today': timezone.now().date(),
                    'error': str(e)
                }
                return render(request, self.template_name, context)
        else:
            logger.warning("No file found in request.FILES")
            messages.error(request, 'No file was uploaded. Please select a PDF file.')
            
            # Re-render the form with error
            context = {
                'letter': engagement_letter,
                'today': timezone.now().date(),
                'error': 'No file was uploaded. Please select a PDF file.'
            }
            return render(request, self.template_name, context)

class MarkEngagementLetterSentView(LoginRequiredMixin, View):
    """View to mark an engagement letter as sent"""

    def get(self, request, letter_id):
        engagement_letter = get_object_or_404(EngagementLetter, id=letter_id)

        # Update status
        engagement_letter.status = 'sent'
        engagement_letter.save()

        messages.success(request, f'Engagement letter for {engagement_letter.association.association_name} marked as sent.')
        return redirect('engagement_letter')


class BulkEngagementLetterView(LoginRequiredMixin, View):
    """View to bulk create engagement letters for a new tax year based on previous year's filings"""
    template_name = 'tax_form/bulk_engagement_letter.html'

    def get(self, request):
        from ..models import Financial, CompletedTaxReturn, ManagementCompany

        current_year = timezone.now().year
        source_year = int(request.GET.get('source_year', current_year - 1))
        target_year = int(request.GET.get('target_year', current_year))
        include_unfiled = request.GET.get('include_unfiled', '') == 'on'

        # Management company filter
        management_company_id = request.GET.get('management_company', '')
        selected_management_company = None
        if management_company_id:
            try:
                selected_management_company = ManagementCompany.objects.get(id=int(management_company_id))
            except (ManagementCompany.DoesNotExist, ValueError):
                pass

        # Check for self-managed filter
        show_self_managed = request.GET.get('self_managed', '') == 'on'

        # Get available years from Financial records
        available_years = Financial.objects.values_list('tax_year', flat=True).distinct().order_by('-tax_year')

        # Get all management companies for the dropdown
        management_companies = ManagementCompany.objects.all().order_by('name')

        # Build preview data - track associations we've already added
        preview_data = []
        added_association_ids = set()

        # First, find associations with filed returns for source year
        filed_returns = CompletedTaxReturn.objects.filter(
            return_filed=True,
            financial__tax_year=source_year
        ).select_related('financial__association')

        for completed_return in filed_returns:
            association = completed_return.financial.association
            added_association_ids.add(association.id)

            # Check if target year engagement letter already exists
            existing_letter = EngagementLetter.objects.filter(
                association=association,
                tax_year=target_year
            ).first()

            # Get source year engagement letter for price
            source_letter = EngagementLetter.objects.filter(
                association=association,
                tax_year=source_year
            ).first()

            price = source_letter.price if source_letter else 150  # Default price

            preview_data.append({
                'association': association,
                'source_letter': source_letter,
                'existing_letter': existing_letter,
                'price': price,
                'can_create': existing_letter is None,
                'return_filed': True,
            })

        # If include_unfiled is checked, also include associations with financials but no filed return
        if include_unfiled:
            # Get all financials for source year
            financials = Financial.objects.filter(tax_year=source_year).select_related('association')
            for financial in financials:
                association = financial.association
                if association.id in added_association_ids:
                    continue  # Skip if already added from filed returns

                added_association_ids.add(association.id)

                # Check if target year engagement letter already exists
                existing_letter = EngagementLetter.objects.filter(
                    association=association,
                    tax_year=target_year
                ).first()

                # Get source year engagement letter for price
                source_letter = EngagementLetter.objects.filter(
                    association=association,
                    tax_year=source_year
                ).first()

                price = source_letter.price if source_letter else 150  # Default price

                preview_data.append({
                    'association': association,
                    'source_letter': source_letter,
                    'existing_letter': existing_letter,
                    'price': price,
                    'can_create': existing_letter is None,
                    'return_filed': False,
                })

        # Filter by management company if selected
        if selected_management_company:
            preview_data = [p for p in preview_data if p['association'].management_company_id == selected_management_company.id]
        elif show_self_managed:
            preview_data = [p for p in preview_data if p['association'].is_self_managed or p['association'].management_company is None]

        # Sort by association name
        preview_data.sort(key=lambda x: x['association'].association_name)

        # Count stats
        total_associations = len(preview_data)
        total_filed = sum(1 for p in preview_data if p.get('return_filed', True))
        can_create_count = sum(1 for p in preview_data if p['can_create'])
        already_exists_count = total_associations - can_create_count

        context = {
            'source_year': source_year,
            'target_year': target_year,
            'available_years': available_years,
            'preview_data': preview_data,
            'total_filed': total_filed,
            'total_associations': total_associations,
            'can_create_count': can_create_count,
            'already_exists_count': already_exists_count,
            'include_unfiled': include_unfiled,
            'management_companies': management_companies,
            'selected_management_company': selected_management_company,
            'show_self_managed': show_self_managed,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        from ..models import Financial, CompletedTaxReturn

        source_year = int(request.POST.get('source_year', timezone.now().year - 1))
        target_year = int(request.POST.get('target_year', timezone.now().year))

        # Get selected association IDs
        selected_ids = request.POST.getlist('selected_associations')

        if not selected_ids:
            messages.warning(request, 'No associations selected.')
            return redirect(f"{request.path}?source_year={source_year}&target_year={target_year}")

        created_count = 0
        skipped_count = 0

        for assoc_id in selected_ids:
            try:
                association = Association.objects.get(id=assoc_id)

                # Check if target year letter already exists
                if EngagementLetter.objects.filter(association=association, tax_year=target_year).exists():
                    skipped_count += 1
                    continue

                # Get source year price
                source_letter = EngagementLetter.objects.filter(
                    association=association,
                    tax_year=source_year
                ).first()
                price = source_letter.price if source_letter else 150

                # Get state fee from source letter or state template
                state_fee = 0
                if source_letter and source_letter.state_fee:
                    state_fee = source_letter.state_fee
                else:
                    # Check for state template default fee
                    filing_state = association.get_filing_state()
                    if filing_state:
                        state_template = StateEngagementTemplate.objects.filter(
                            state=filing_state,
                            is_active=True
                        ).first()
                        if state_template:
                            state_fee = state_template.default_state_fee

                # Create new engagement letter
                EngagementLetter.objects.create(
                    association=association,
                    tax_year=target_year,
                    price=price,
                    state_fee=state_fee,
                    status='pending'
                )
                created_count += 1

            except Association.DoesNotExist:
                logger.warning(f"Association {assoc_id} not found during bulk creation")
                continue
            except Exception as e:
                logger.error(f"Error creating engagement letter for association {assoc_id}: {e}")
                continue

        if created_count > 0:
            messages.success(request, f'Successfully created {created_count} engagement letter(s) for {target_year}.')
        if skipped_count > 0:
            messages.info(request, f'Skipped {skipped_count} association(s) that already had {target_year} engagement letters.')

        return redirect('engagement_letter')


class EngagementLetterTemplateView(LoginRequiredMixin, View):
    """View to edit the base engagement letter template for a tax year"""
    template_name = 'tax_form/engagement_letter_template.html'

    def get(self, request):
        current_year = timezone.now().year
        selected_year = int(request.GET.get('year', current_year))

        # Get or create template for selected year
        template, created = EngagementLetterTemplate.objects.get_or_create(
            tax_year=selected_year,
            defaults={'default_price': 150}
        )

        # Get available years
        available_years = list(range(current_year - 2, current_year + 2))

        context = {
            'template': template,
            'selected_year': selected_year,
            'available_years': available_years,
            'created': created,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        selected_year = int(request.POST.get('tax_year', timezone.now().year))

        template, created = EngagementLetterTemplate.objects.get_or_create(
            tax_year=selected_year
        )

        # Update template fields
        template.services_text = request.POST.get('services_text', template.services_text)
        template.fees_text = request.POST.get('fees_text', template.fees_text)
        template.responsibilities_text = request.POST.get('responsibilities_text', template.responsibilities_text)
        template.consent_text = request.POST.get('consent_text', template.consent_text)
        template.default_price = int(request.POST.get('default_price', 150))
        template.save()

        messages.success(request, f'Template for {selected_year} saved successfully.')
        return redirect(f"{request.path}?year={selected_year}")


class EditEngagementLetterView(LoginRequiredMixin, View):
    """View to edit an individual engagement letter"""
    template_name = 'tax_form/edit_engagement_letter.html'

    def get(self, request, letter_id):
        letter = get_object_or_404(EngagementLetter, id=letter_id)
        template = letter.get_template()

        context = {
            'letter': letter,
            'template': template,
            'services_text': letter.custom_services_text or (template.services_text.replace('{tax_year}', str(letter.tax_year)) if template else ''),
            'fees_text': letter.custom_fees_text or (template.fees_text if template else ''),
            'responsibilities_text': letter.custom_responsibilities_text or (template.responsibilities_text if template else ''),
            'consent_text': letter.custom_consent_text or (template.consent_text if template else ''),
        }
        return render(request, self.template_name, context)

    def post(self, request, letter_id):
        letter = get_object_or_404(EngagementLetter, id=letter_id)

        # Check if using custom or template
        use_custom = request.POST.get('use_custom_text') == 'on'

        # Update price and state fee (handle decimal input)
        price_value = request.POST.get('price', str(letter.price))
        letter.price = int(float(price_value)) if price_value else letter.price
        state_fee_value = request.POST.get('state_fee', str(letter.state_fee))
        letter.state_fee = int(float(state_fee_value)) if state_fee_value else 0

        if use_custom:
            letter.custom_services_text = request.POST.get('services_text', '')
            letter.custom_fees_text = request.POST.get('fees_text', '')
            letter.custom_responsibilities_text = request.POST.get('responsibilities_text', '')
            letter.custom_consent_text = request.POST.get('consent_text', '')
        else:
            # Clear custom text to use template
            letter.custom_services_text = None
            letter.custom_fees_text = None
            letter.custom_responsibilities_text = None
            letter.custom_consent_text = None

        letter.save()

        messages.success(request, f'Engagement letter for {letter.association.association_name} updated.')
        return redirect('engagement_letter')


class PreviewEngagementLetterView(LoginRequiredMixin, View):
    """View to preview an engagement letter PDF without downloading"""

    def get(self, request, letter_id):
        letter = get_object_or_404(EngagementLetter, id=letter_id)

        # Generate PDF using the updated method
        pdf_response = self.generate_preview_pdf(letter)

        # Return as inline PDF (opens in browser)
        response = HttpResponse(pdf_response, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="preview_{letter.association.association_name}_{letter.tax_year}.pdf"'
        return response

    def generate_preview_pdf(self, engagement_letter):
        """Generate a PDF engagement letter using template/custom text"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=50, leftMargin=50,
                                topMargin=50, bottomMargin=50)

        styles = getSampleStyleSheet()
        elements = []

        # Header with logo
        logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'dynamite_logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path)
            logo.drawHeight = 0.8*inch
            logo.drawWidth = 2*inch

            company_header = Paragraph("""
            <para align="right">
            <b>Dynamite Management, LLC</b><br/>
            PO Box 8, Vancouver, WA 98666<br/>
            Phone: 360-524-9665<br/>
            Email: info@hoafiscal.com
            </para>""", styles['Normal'])

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
            company_header = Paragraph("""
            <para align="right">
            <b>Dynamite Management, LLC</b><br/>
            PO Box 8, Vancouver, WA 98666<br/>
            Phone: 360-524-9665<br/>
            Email: info@hoafiscal.com
            </para>""", styles['Normal'])
            elements.append(company_header)

        elements.append(Spacer(1, 0.5*inch))

        # Introduction
        intro = f"""We are pleased to confirm our understanding of the services we are to provide for:
        <b>{engagement_letter.association.association_name}</b>, for the year ended December 31, {engagement_letter.tax_year}.
        This letter sets forth the terms of our engagement."""
        elements.append(Paragraph(intro, styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))

        # Services section - use template/custom text
        services = f"<b>Services Provided:</b><br/>{engagement_letter.get_services_text()}"
        elements.append(Paragraph(services, styles['Normal']))

        # State-specific services (if applicable)
        state_services = engagement_letter.get_state_services_text()
        if state_services:
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(state_services, styles['Normal']))

        elements.append(Spacer(1, 0.25*inch))

        # Fees section - use template/custom text
        fees = f"<b>Fees:</b><br/>{engagement_letter.get_fees_text()}"
        elements.append(Paragraph(fees, styles['Normal']))

        # State fee (if applicable)
        state_fee_text = engagement_letter.get_state_fee_text()
        if state_fee_text:
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(state_fee_text, styles['Normal']))

        # Total fee (if there's a state fee)
        if engagement_letter.state_fee > 0:
            elements.append(Spacer(1, 0.1*inch))
            total = engagement_letter.get_total_fee()
            elements.append(Paragraph(f"<b>Total Fee: ${total}</b>", styles['Normal']))

        elements.append(Spacer(1, 0.25*inch))

        # Responsibilities section
        responsibilities_text = engagement_letter.get_responsibilities_text()
        if responsibilities_text:
            responsibilities = f"<b>Responsibilities:</b><br/>{responsibilities_text}"
            elements.append(Paragraph(responsibilities, styles['Normal']))
            elements.append(Spacer(1, 0.25*inch))

        # Consent section
        consent_text = engagement_letter.get_consent_text()
        if consent_text:
            consent = f"<b>Consent to Use of Tax Return Information:</b><br/>{consent_text}"
            elements.append(Paragraph(consent, styles['Normal']))
            elements.append(Spacer(1, 0.25*inch))

        # State disclosure section (if applicable)
        state_disclosure = engagement_letter.get_state_disclosure_text()
        if state_disclosure:
            state_template = engagement_letter.get_state_template()
            state_name = state_template.get_state_name() if state_template else engagement_letter.association.state
            disclosure = f"<b>{state_name} State Disclosure:</b><br/>{state_disclosure}"
            elements.append(Paragraph(disclosure, styles['Normal']))
            elements.append(Spacer(1, 0.25*inch))

        # Signature section
        signature = """To indicate your agreement to the arrangements above, please sign and date this letter."""
        elements.append(Paragraph(signature, styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))

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

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf


class DownloadCombinedEngagementLettersView(LoginRequiredMixin, View):
    """View to download multiple engagement letters as a single combined PDF"""

    def post(self, request):
        from PyPDF2 import PdfMerger

        letter_ids_str = request.POST.get('letter_ids', '')
        if not letter_ids_str:
            messages.error(request, 'No engagement letters selected.')
            return redirect('engagement_letter')

        letter_ids = [int(id) for id in letter_ids_str.split(',') if id.strip().isdigit()]
        if not letter_ids:
            messages.error(request, 'Invalid engagement letter selection.')
            return redirect('engagement_letter')

        # Get the letters in order
        letters = EngagementLetter.objects.filter(id__in=letter_ids).order_by('association__association_name')

        if not letters.exists():
            messages.error(request, 'No engagement letters found.')
            return redirect('engagement_letter')

        # Create PDF merger
        merger = PdfMerger()
        preview_view = PreviewEngagementLetterView()

        try:
            for letter in letters:
                # Generate PDF for each letter
                pdf_content = preview_view.generate_pdf(letter)
                pdf_buffer = BytesIO(pdf_content)
                merger.append(pdf_buffer)

            # Write combined PDF to buffer
            output_buffer = BytesIO()
            merger.write(output_buffer)
            merger.close()

            output_buffer.seek(0)
            combined_pdf = output_buffer.getvalue()

            # Determine filename
            if letters.count() == 1:
                filename = f"engagement_letter_{letters.first().association.association_name[:20]}_{letters.first().tax_year}.pdf"
            else:
                tax_years = letters.values_list('tax_year', flat=True).distinct()
                if len(set(tax_years)) == 1:
                    filename = f"engagement_letters_{list(tax_years)[0]}_{letters.count()}_letters.pdf"
                else:
                    filename = f"engagement_letters_combined_{letters.count()}_letters.pdf"

            # Clean filename
            filename = ''.join(c for c in filename if c.isalnum() or c in '._-')

            response = HttpResponse(combined_pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            logger.error(f"Error generating combined PDF: {str(e)}", exc_info=True)
            messages.error(request, f"Error generating combined PDF: {str(e)}")
            return redirect('engagement_letter')


class StateEngagementTemplateListView(LoginRequiredMixin, View):
    """View to list and manage state engagement templates"""
    template_name = 'tax_form/state_engagement_templates.html'

    def get(self, request):
        # Get all state templates
        state_templates = StateEngagementTemplate.objects.all()

        # Get states that don't have templates yet
        existing_states = set(state_templates.values_list('state', flat=True))
        available_states = [
            (code, name) for code, name in StateEngagementTemplate.STATE_CHOICES
            if code not in existing_states
        ]

        context = {
            'state_templates': state_templates,
            'available_states': available_states,
        }
        return render(request, self.template_name, context)


class StateEngagementTemplateEditView(LoginRequiredMixin, View):
    """View to edit a state engagement template"""
    template_name = 'tax_form/edit_state_template.html'

    def get(self, request, state_code=None):
        if state_code:
            template = get_object_or_404(StateEngagementTemplate, state=state_code)
            is_new = False
        else:
            # Creating new template
            state_code = request.GET.get('state')
            if not state_code:
                messages.error(request, 'State code is required.')
                return redirect('state_engagement_templates')
            template = StateEngagementTemplate(state=state_code)
            is_new = True

        context = {
            'template': template,
            'is_new': is_new,
            'state_name': dict(StateEngagementTemplate.STATE_CHOICES).get(state_code, state_code),
        }
        return render(request, self.template_name, context)

    def post(self, request, state_code=None):
        if state_code:
            template = get_object_or_404(StateEngagementTemplate, state=state_code)
        else:
            state_code = request.POST.get('state')
            template, created = StateEngagementTemplate.objects.get_or_create(state=state_code)

        # Update fields
        template.is_active = request.POST.get('is_active') == 'on'
        template.state_form_name = request.POST.get('state_form_name', '')
        template.state_services_text = request.POST.get('state_services_text', '')
        # Handle decimal input by converting to float first, then int
        fee_value = request.POST.get('default_state_fee', '0')
        template.default_state_fee = int(float(fee_value)) if fee_value else 0
        template.state_fee_text = request.POST.get('state_fee_text', '')
        template.state_disclosure_text = request.POST.get('state_disclosure_text', '')
        template.save()

        messages.success(request, f'State template for {template.get_state_display()} saved successfully.')
        return redirect('state_engagement_templates')


class StateEngagementTemplateDeleteView(LoginRequiredMixin, View):
    """View to delete a state engagement template"""

    def post(self, request, state_code):
        template = get_object_or_404(StateEngagementTemplate, state=state_code)
        state_name = template.get_state_display()
        template.delete()
        messages.success(request, f'State template for {state_name} deleted.')
        return redirect('state_engagement_templates')