"""
URL configuration for HOA_tax project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tax_form.urls')),
    # Add explicit media serving for both development and production
    path('media/<path:path>', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

# For local development only - this is already handled by the serve view above
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)