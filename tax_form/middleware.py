import logging

logger = logging.getLogger(__name__)

class AssociationSessionMiddleware:
    """Middleware to handle association and tax year persistence across views."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request before the view is called
        
        # Check if we have association_id and tax_year in GET parameters
        association_id = request.GET.get('association_id')
        tax_year = request.GET.get('tax_year')
        
        # If we have association_id in the request, update the session
        if association_id:
            request.session['selected_association_id'] = association_id
            logger.debug(f"Storing association_id {association_id} in session")
        
        # If we have tax_year in the request, update the session
        if tax_year:
            try:
                # Ensure tax_year is a valid integer
                tax_year_int = int(tax_year)
                request.session['selected_tax_year'] = tax_year_int
                logger.debug(f"Storing tax_year {tax_year_int} in session")
            except (ValueError, TypeError):
                # If tax_year is not a valid integer, don't update the session
                logger.warning(f"Invalid tax_year value: {tax_year}")
        
        # Process the response
        response = self.get_response(request)
        return response