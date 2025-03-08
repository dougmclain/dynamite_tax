# Create a new file: tax_form/utils/session_management.py

def save_selection_to_session(request, association_id=None, tax_year=None):
    """
    Save current association and tax year selection to session.
    
    Args:
        request: The current request
        association_id: The ID of the selected association (optional)
        tax_year: The selected tax year (optional)
    """
    if association_id:
        request.session['selected_association_id'] = association_id
        
    if tax_year:
        request.session['selected_tax_year'] = str(tax_year)
    
def get_selection_from_session(request):
    """
    Get the saved association and tax year selection from session.
    
    Args:
        request: The current request
        
    Returns:
        tuple: (association_id, tax_year)
    """
    association_id = request.session.get('selected_association_id')
    tax_year = request.session.get('selected_tax_year')
    
    return association_id, tax_year