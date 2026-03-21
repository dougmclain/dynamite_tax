import base64
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings
import anthropic

logger = logging.getLogger(__name__)


AMOUNT_FIELDS = [
    'member_assessments', 'capital_contribution', 'moving_fees', 'utilities',
    'late_fees', 'fines', 'other_exempt_income',
    'interest', 'dividends', 'rentals',
    'non_exempt_income_amount1', 'non_exempt_income_amount2', 'non_exempt_income_amount3',
    'total_expenses', 'tax_preparation', 'management_fees', 'administration_fees',
    'audit_fees', 'allocated_rental_expenses',
    'non_exempt_expense_amount1', 'non_exempt_expense_amount2', 'non_exempt_expense_amount3',
    'prior_year_over_payment', 'extension_payment', 'estimated_payment',
]

DESCRIPTION_FIELDS = [
    'non_exempt_income_description1', 'non_exempt_income_description2',
    'non_exempt_income_description3',
    'non_exempt_expense_description1', 'non_exempt_expense_description2',
    'non_exempt_expense_description3',
]

EXTRACTION_PROMPT = """You are a tax accountant assistant. Analyze this HOA (Homeowners Association) financial document and extract the financial data.

Return ONLY a JSON object with the following fields. Use whole dollar amounts (no cents, no dollar signs, no commas). If a value cannot be found in the document, use 0 for amounts or "" for descriptions.

EXEMPT INCOME (income from members that is exempt from tax):
- "member_assessments": Regular HOA dues/assessments collected from members
- "capital_contribution": Capital contributions or special assessments for capital improvements
- "moving_fees": Move-in/move-out fees
- "utilities": Utility reimbursements from members
- "late_fees": Late fees or penalties charged to members
- "fines": Fines for rule violations
- "other_exempt_income": Any other exempt function income not categorized above

NON-EXEMPT INCOME (investment/non-member income that IS taxable):
- "interest": Interest income (bank interest, CD interest, etc.)
- "dividends": Dividend income
- "rentals": Rental income from common areas, cell towers, laundry, vending, etc.
- "non_exempt_income_description1": Description of first other non-exempt income source
- "non_exempt_income_amount1": Amount of first other non-exempt income
- "non_exempt_income_description2": Description of second other non-exempt income source
- "non_exempt_income_amount2": Amount of second other non-exempt income
- "non_exempt_income_description3": Description of third other non-exempt income source
- "non_exempt_income_amount3": Amount of third other non-exempt income

EXPENSES:
- "total_expenses": Total operating expenses for the year
- "tax_preparation": Tax preparation fees
- "management_fees": Management company fees
- "administration_fees": Administrative/office expenses
- "audit_fees": Audit or accounting fees
- "allocated_rental_expenses": Expenses directly related to rental income
- "non_exempt_expense_description1": Description of first other deductible expense
- "non_exempt_expense_amount1": Amount of first other deductible expense
- "non_exempt_expense_description2": Description of second other deductible expense
- "non_exempt_expense_amount2": Amount of second other deductible expense
- "non_exempt_expense_description3": Description of third other deductible expense
- "non_exempt_expense_amount3": Amount of third other deductible expense

PAYMENTS:
- "prior_year_over_payment": Overpayment from prior year applied to this year
- "extension_payment": Payment made with extension
- "estimated_payment": Estimated tax payments made during the year

IMPORTANT GUIDANCE:
1. "member_assessments" is usually the largest line item. It may be labeled "Assessment Income", "HOA Dues", "Member Assessments", "Maintenance Fees", or similar.
2. "total_expenses" should be the grand total of ALL operating expenses, not just a subtotal.
3. For non-exempt income: look for interest, dividends, and any rental/non-member income.
4. Rental income includes laundry income, vending machine income, cell tower leases, parking rentals, and similar non-member revenue.
5. If the document shows a P&L or Income Statement, use the annual totals (not monthly).
6. If you see "Budget" and "Actual" columns, use the "Actual" column.

CRITICAL - DOLLAR AMOUNTS:
- Return whole dollar amounts ONLY. Round cents to the nearest dollar.
- Do NOT include cents. Do NOT multiply by 100. Do NOT append "00" for cents.
- Examples of CORRECT conversion:
  "$12,444.00" → 12444
  "$5.01" → 5
  "$2,506.69" → 2507
  "$11,759.96" → 11760
  "$462.00" → 462
  "$259.11" → 259
- Examples of WRONG conversion (DO NOT do this):
  "$12,444.00" → 1244400  (WRONG - this treats cents as dollars)
  "$5.01" → 501  (WRONG - this removes the decimal point instead of rounding)
- Simply take the dollar amount before the decimal point and round up if cents >= 50.

Return ONLY the JSON object, no other text."""


def build_management_company_context(management_company):
    """Build additional prompt context from management company hints and past corrections."""
    sections = []

    if management_company.extraction_hints:
        sections.append(
            f"MANAGEMENT COMPANY: {management_company.name}\n"
            f"EXTRACTION HINTS FROM USER:\n{management_company.extraction_hints}"
        )
    else:
        sections.append(f"MANAGEMENT COMPANY: {management_company.name}")

    # Get recent corrections as few-shot training examples (limit to most recent 20)
    corrections = management_company.extraction_corrections.order_by('-created_at')[:20]
    if corrections.exists():
        correction_lines = []
        for c in corrections:
            line = f'- Field "{c.field_name}": AI extracted "{c.ai_value}" but correct value was "{c.corrected_value}"'
            if c.source_label:
                line += f' (PDF label: "{c.source_label}")'
            if c.notes:
                line += f' — Note: {c.notes}'
            correction_lines.append(line)

        sections.append(
            "PAST CORRECTIONS FOR THIS MANAGEMENT COMPANY (learn from these):\n"
            "The following are past mistakes the AI made on this company's reports. "
            "Use these to avoid repeating the same errors:\n"
            + "\n".join(correction_lines)
        )

    return "\n\n".join(sections)


def sanitize_extracted_data(data):
    sanitized = {}
    for field in AMOUNT_FIELDS:
        val = data.get(field, 0)
        try:
            # Handle string values that might have dollar signs, commas, or decimals
            if isinstance(val, str):
                val = val.replace('$', '').replace(',', '').strip()
            # Convert to float first — this correctly handles "12444.00" → 12444.0
            val = int(round(float(val)))
            val = max(0, val)
        except (ValueError, TypeError):
            val = 0
        sanitized[field] = val

    for field in DESCRIPTION_FIELDS:
        val = data.get(field, '')
        if not isinstance(val, str):
            val = str(val) if val else ''
        sanitized[field] = val[:100]

    return sanitized


@login_required
@require_POST
def extract_financial_from_pdf(request):
    if 'pdf_file' not in request.FILES:
        return JsonResponse({'error': 'No PDF file provided.'}, status=400)

    pdf_file = request.FILES['pdf_file']

    if not pdf_file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': 'File must be a PDF.'}, status=400)

    MAX_SIZE = 10 * 1024 * 1024
    if pdf_file.size > MAX_SIZE:
        return JsonResponse({'error': 'File too large. Maximum size is 10MB.'}, status=400)

    pdf_bytes = pdf_file.read()
    pdf_base64 = base64.standard_b64encode(pdf_bytes).decode('utf-8')

    # Save the PDF to the Financial instance if we have context
    association_id = request.POST.get('association_id')
    tax_year = request.POST.get('tax_year')

    management_company = None
    if association_id:
        from ..models import Association
        try:
            association = Association.objects.select_related('management_company').get(id=association_id)
            if not association.is_self_managed and association.management_company:
                management_company = association.management_company
        except Association.DoesNotExist:
            pass

    if association_id and tax_year:
        from ..models import Financial
        try:
            financial = Financial.objects.get(
                association_id=association_id, tax_year=tax_year
            )
            pdf_file.seek(0)
            financial.financial_info_pdf.save(pdf_file.name, pdf_file, save=True)
        except Financial.DoesNotExist:
            pass

    # Build the prompt — base + management company context if available
    prompt = EXTRACTION_PROMPT
    if management_company:
        company_context = build_management_company_context(management_company)
        prompt = prompt + "\n\n" + company_context

    # Call Claude API
    try:
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return JsonResponse({'error': 'Anthropic API key not configured.'}, status=500)

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        response_text = message.content[0].text

        # Extract JSON from response (handle markdown code fences)
        json_str = response_text
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]

        extracted_data = json.loads(json_str.strip())
        sanitized = sanitize_extracted_data(extracted_data)

        return JsonResponse({
            'success': True,
            'data': sanitized,
            'management_company_id': management_company.id if management_company else None,
        })

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: status={e.status_code}, message={e.message}, body={e.body}", exc_info=True)
        return JsonResponse({
            'error': f'AI service error: {str(e)}'
        }, status=502)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse Claude response: {response_text}", exc_info=True)
        return JsonResponse({
            'error': 'Could not parse AI response. Please try again.'
        }, status=500)
    except Exception as e:
        logger.error(f"Extraction error: {e}", exc_info=True)
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@require_POST
def save_extraction_corrections(request):
    """Save corrections when user modifies AI-extracted values before saving."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    management_company_id = data.get('management_company_id')
    corrections = data.get('corrections', [])
    tax_year = data.get('tax_year')

    if not management_company_id or not corrections or not tax_year:
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    from ..models import ManagementCompany, ExtractionCorrection

    try:
        management_company = ManagementCompany.objects.get(id=management_company_id)
    except ManagementCompany.DoesNotExist:
        return JsonResponse({'error': 'Management company not found'}, status=404)

    created_count = 0
    for correction in corrections:
        field_name = correction.get('field_name', '')
        ai_value = str(correction.get('ai_value', ''))
        corrected_value = str(correction.get('corrected_value', ''))

        if not field_name or ai_value == corrected_value:
            continue

        ExtractionCorrection.objects.create(
            management_company=management_company,
            field_name=field_name,
            ai_value=ai_value,
            corrected_value=corrected_value,
            tax_year=tax_year,
        )
        created_count += 1

    return JsonResponse({'success': True, 'corrections_saved': created_count})
