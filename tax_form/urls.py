from django.urls import path
from django.contrib.auth import views as auth_views
from .views import main, association, financial, create_association, dashboard, edit_association, edit_tax_year_info, extension, engagement_letter, filing_status

urlpatterns = [
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
    path('engagement-letter/download/<int:letter_id>/', engagement_letter.DownloadEngagementLetterView.as_view(), name='download_engagement_letter'),
    path('engagement-letter/delete/<int:letter_id>/', engagement_letter.DeleteEngagementLetterView.as_view(), name='delete_engagement_letter'),
    path('engagement-letter/upload-signed/<int:letter_id>/', engagement_letter.UploadSignedEngagementLetterView.as_view(), name='upload_signed_engagement_letter'),
    path('engagement-letter/mark-sent/<int:letter_id>/', engagement_letter.MarkEngagementLetterSentView.as_view(), name='mark_sent_engagement_letter'),
# Add this to your existing urlpatterns list in tax_form/urls.py
    path('filing-status/<int:association_id>/<int:tax_year>/', 
        filing_status.EditFilingStatusView.as_view(), name='edit_filing_status'),
]