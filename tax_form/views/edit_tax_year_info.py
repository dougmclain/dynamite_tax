from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import Http404
from ..models import Association, Financial, Extension, CompletedTaxReturn
from django.core.files.storage import default_storage

class EditTaxYearInfoView(View):
    template_name = 'tax_form/edit_tax_year_info.html'

    def get(self, request, association_id, tax_year):
        association = get_object_or_404(Association, id=association_id)
        financial, created = Financial.objects.get_or_create(
            association=association,
            tax_year=tax_year,
            defaults={'total_expenses': 0}
        )
        extension, _ = Extension.objects.get_or_create(financial=financial)
        completed_tax_return, _ = CompletedTaxReturn.objects.get_or_create(financial=financial)

        context = {
            'association': association,
            'tax_year': tax_year,
            'extension': extension,
            'completed_tax_return': completed_tax_return,
        }
        return render(request, self.template_name, context)

    def post(self, request, association_id, tax_year):
        try:
            association = get_object_or_404(Association, id=association_id)
            financial, created = Financial.objects.get_or_create(
                association=association,
                tax_year=tax_year,
                defaults={'total_expenses': 0}
            )
            extension, _ = Extension.objects.get_or_create(financial=financial)
            completed_tax_return, _ = CompletedTaxReturn.objects.get_or_create(financial=financial)

            extension.filed = 'extension_filed' in request.POST
            extension.filed_date = request.POST.get('extension_filed_date') or None
            completed_tax_return.return_filed = 'tax_return_filed' in request.POST
            completed_tax_return.date_prepared = request.POST.get('tax_return_filed_date') or None

            if 'extension_file' in request.FILES:
                if extension.form_7004:
                    default_storage.delete(extension.form_7004.path)
                extension.form_7004 = request.FILES['extension_file']

            if 'tax_return_file' in request.FILES:
                if completed_tax_return.tax_return_pdf:
                    default_storage.delete(completed_tax_return.tax_return_pdf.path)
                completed_tax_return.tax_return_pdf = request.FILES['tax_return_file']

            extension.save()
            completed_tax_return.save()

            messages.success(request, f'Tax year {tax_year} information updated successfully.')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect(f"{reverse('association')}?association_id={association_id}&tax_year={tax_year}")