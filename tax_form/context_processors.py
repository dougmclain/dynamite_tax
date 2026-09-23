from django.conf import settings


def site_info(request):
    """Public contact details used by the landing page, login page and app footer."""
    return {
        'site_contact_email': settings.SITE_CONTACT_EMAIL,
        'site_contact_phone': settings.SITE_CONTACT_PHONE,
    }
