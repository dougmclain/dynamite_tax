from django.urls import path
from django.contrib.auth import views as auth_views
from .views import main, association, financial, create_association, dashboard, edit_association, edit_tax_year_info, extension

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
    path('accounts/login/', auth_views.LoginView.as_view(template_name='tax_form/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]