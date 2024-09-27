from django.urls import path
from .views import main, association, financial

urlpatterns = [
    path('', main.index, name='index'),
    path('form-1120h/', main.form_1120h, name='form_1120h'),
    path('create-association/', association.create_association, name='create_association'),
    path('create-financial/', financial.create_financial, name='create_financial'),
]