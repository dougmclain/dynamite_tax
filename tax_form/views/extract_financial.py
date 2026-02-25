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
5. Round all amounts to whole dollars.
6. If the document shows a P&L or Income Statement, use the annual totals (not monthly).
7. If you see "Budget" and "Actual" columns, use the "Actual" column.

Return ONLY the JSON object, no other text."""


def sanitize_extracted_data(data):
    sanitized = {}
    for field in AMOUNT_FIELDS:
        val = data.get(field, 0)
        try:
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
                            "text": EXTRACTION_PROMPT,
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
