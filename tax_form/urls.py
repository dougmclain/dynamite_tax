# Update tax_form/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from .views import main, association, financial, create_association, dashboard, edit_association, edit_tax_year_info, extension, engagement_letter, filing_status, management_company
from .views.delete_files import DeleteFinancialPDFView
from .views.export import ExportAssociationsView, ExportCompletedReturnsExcelView

urlpatterns = [
    # Existing URLs
    path('', main.index, name='index'),
    path('form-1120h/', main.form_1120h, name='form_1120h'),
    path('association/', association.AssociationView.as_view(), name='association'),
    path('create-association/', create_association.CreateAssociationView.as_view(), name='create_association'),
    path('create-financial/', financial.create_financial, name='create_financial'),
    path('dashboard/', dashboard.DashboardView.as_view(), name='dashboard'),
    path('edit-association/<int:association_id>/', edit_association.EditAssociationView.as_view(), name='edit_association'),
    path('edit-tax-year-info/<int:association_id>/<int:tax_year>/', edit_tax_year_info.EditTaxYearInfoView.as_view(), name='edit_tax_year_info'),
    path('extension-form/', extension.ExtensionFormView.as_view(), name='extension_form'),
    path('admin/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('admin/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('engagement-letter/', engagement_letter.EngagementLetterView.as_view(), name='engagement_letter'),
    path('engagement-letter/bulk-create/', engagement_letter.BulkEngagementLetterView.as_view(), name='bulk_engagement_letter'),
    path('engagement-letter/template/', engagement_letter.EngagementLetterTemplateView.as_view(), name='engagement_letter_template'),
    path('engagement-letter/state-templates/', engagement_letter.StateEngagementTemplateListView.as_view(), name='state_engagement_templates'),
    path('engagement-letter/state-templates/new/', engagement_letter.StateEngagementTemplateEditView.as_view(), name='state_engagement_template_new'),
    path('engagement-letter/state-templates/<str:state_code>/', engagement_letter.StateEngagementTemplateEditView.as_view(), name='state_engagement_template_edit'),
    path('engagement-letter/state-templates/<str:state_code>/delete/', engagement_letter.StateEngagementTemplateDeleteView.as_view(), name='state_engagement_template_delete'),
    path('engagement-letter/edit/<int:letter_id>/', engagement_letter.EditEngagementLetterView.as_view(), name='edit_engagement_letter'),
    path('engagement-letter/preview/<int:letter_id>/', engagement_letter.PreviewEngagementLetterView.as_view(), name='preview_engagement_letter'),
    path('engagement-letter/download/<int:letter_id>/', engagement_letter.DownloadEngagementLetterView.as_view(), name='download_engagement_letter'),
    path('engagement-letter/delete/<int:letter_id>/', engagement_letter.DeleteEngagementLetterView.as_view(), name='delete_engagement_letter'),
    path('engagement-letter/upload-signed/<int:letter_id>/', engagement_letter.UploadSignedEngagementLetterView.as_view(), name='upload_signed_engagement_letter'),
    path('engagement-letter/mark-sent/<int:letter_id>/', engagement_letter.MarkEngagementLetterSentView.as_view(), name='mark_sent_engagement_letter'),
    path('engagement-letter/download-combined/', engagement_letter.DownloadCombinedEngagementLettersView.as_view(), name='download_combined_engagement_letters'),
    path('filing-status/<int:association_id>/<int:tax_year>/', filing_status.EditFilingStatusView.as_view(), name='edit_filing_status'),
    path('delete-financial-pdf/<int:financial_id>/', DeleteFinancialPDFView.as_view(), name='delete_financial_pdf'),
    
    # Management Company URLs
    path('management-companies/', management_company.ManagementCompanyListView.as_view(), name='management_company_list'),
    path('management-companies/create/', management_company.ManagementCompanyCreateView.as_view(), name='management_company_create'),
    path('management-companies/<int:pk>/', management_company.ManagementCompanyDetailView.as_view(), name='management_company_detail'),
    path('management-companies/<int:pk>/edit/', management_company.ManagementCompanyUpdateView.as_view(), name='management_company_update'),
    path('management-companies/<int:pk>/delete/', management_company.ManagementCompanyDeleteView.as_view(), name='management_company_delete'),
    path('export-associations/', ExportAssociationsView.as_view(), name='export_associations'),
    path('export-completed-returns/', ExportCompletedReturnsExcelView.as_view(), name='export_completed_returns'),
]