from django.urls import path
from .views import main, association, financial, create_association

urlpatterns = [
    path('', main.index, name='index'),
    path('form-1120h/', main.form_1120h, name='form_1120h'),
    path('association/', association.AssociationView.as_view(), name='association'),
    path('create-association/', create_association.CreateAssociationView.as_view(), name='create_association'),
    path('create-financial/', financial.create_financial, name='create_financial'),
]