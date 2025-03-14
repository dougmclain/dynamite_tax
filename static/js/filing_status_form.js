// static/js/filing_status_form.js

document.addEventListener('DOMContentLoaded', function() {
    const prepareReturnCheckbox = document.getElementById('id_prepare_return');
    const reasonContainer = document.getElementById('reason-container');
    
    if (prepareReturnCheckbox && reasonContainer) {
        function toggleReasonVisibility() {
            if (prepareReturnCheckbox.checked) {
                reasonContainer.style.display = 'none';
            } else {
                reasonContainer.style.display = 'block';
            }
        }
        
        // Set initial state
        toggleReasonVisibility();
        
        // Add event listener for changes
        prepareReturnCheckbox.addEventListener('change', toggleReasonVisibility);
    }
});