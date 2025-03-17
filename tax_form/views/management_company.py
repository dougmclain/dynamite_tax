# Create a new file: tax_form/views/management_company.py

from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from ..models import ManagementCompany
from ..forms import ManagementCompanyForm
import logging

logger = logging.getLogger(__name__)

class ManagementCompanyListView(LoginRequiredMixin, ListView):
    """View to list all management companies."""
    model = ManagementCompany
    template_name = 'tax_form/management_company/list.html'
    context_object_name = 'management_companies'

class ManagementCompanyDetailView(LoginRequiredMixin, DetailView):
    """View to show details of a management company."""
    model = ManagementCompany
    template_name = 'tax_form/management_company/detail.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add associations to context
        context['associations'] = self.object.associations.all().order_by('association_name')
        return context

class ManagementCompanyCreateView(LoginRequiredMixin, CreateView):
    """View to create a new management company."""
    model = ManagementCompany
    form_class = ManagementCompanyForm
    template_name = 'tax_form/management_company/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Management Company'
        context['action'] = 'Create'
        return context
    
    def form_valid(self, form):
        # Check if this is an AJAX request from the modal
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                company = form.save()
                return JsonResponse({
                    'success': True,
                    'id': company.id,
                    'name': company.name
                })
            except Exception as e:
                logger.error(f"Error creating management company: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
        
        # Normal form submission
        messages.success(self.request, 'Management company created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('management_company_list')

class ManagementCompanyUpdateView(LoginRequiredMixin, UpdateView):
    """View to update a management company."""
    model = ManagementCompany
    form_class = ManagementCompanyForm
    template_name = 'tax_form/management_company/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Management Company'
        context['action'] = 'Update'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Management company updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('management_company_detail', kwargs={'pk': self.object.pk})

class ManagementCompanyDeleteView(LoginRequiredMixin, DeleteView):
    """View to delete a management company."""
    model = ManagementCompany
    template_name = 'tax_form/management_company/confirm_delete.html'
    success_url = reverse_lazy('management_company_list')
    context_object_name = 'company'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Management company deleted successfully.')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add associations count to context
        context['associations_count'] = self.object.associations.count()
        return context