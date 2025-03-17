// static/js/management_company.js

document.addEventListener('DOMContentLoaded', function() {
    // Get references to form elements
    const selfManagedCheckbox = document.getElementById('id_is_self_managed');
    const managementCompanySelect = document.getElementById('id_management_company');
    const managementCompanyFormGroup = managementCompanySelect?.closest('.form-group') || 
                                       managementCompanySelect?.closest('.mb-3');

    // If elements exist, set up the toggle behavior
    if (selfManagedCheckbox && managementCompanySelect && managementCompanyFormGroup) {
        // Function to toggle management company visibility based on self-managed status
        const toggleManagementCompany = function() {
            if (selfManagedCheckbox.checked) {
                // If self-managed, hide management company field and clear selection
                managementCompanyFormGroup.style.display = 'none';
                managementCompanySelect.value = '';
            } else {
                // If not self-managed, show management company field
                managementCompanyFormGroup.style.display = 'block';
            }
        };

        // Set initial state
        toggleManagementCompany();

        // Add event listener for changes
        selfManagedCheckbox.addEventListener('change', toggleManagementCompany);
    }

    // Set up modal for adding a new management company if elements exist
    const newManagementCompanyBtn = document.getElementById('new-management-company-btn');
    const managementCompanyModal = document.getElementById('management-company-modal');
    
    if (newManagementCompanyBtn && managementCompanyModal) {
        // Initialize modal if Bootstrap JS is loaded
        if (typeof bootstrap !== 'undefined') {
            const modal = new bootstrap.Modal(managementCompanyModal);
            
            // Show modal when button is clicked
            newManagementCompanyBtn.addEventListener('click', function() {
                modal.show();
            });
            
            // Handle form submission in modal
            const modalForm = managementCompanyModal.querySelector('form');
            if (modalForm) {
                modalForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    // Get form data
                    const formData = new FormData(modalForm);
                    
                    // Send AJAX request to create management company
                    fetch(modalForm.getAttribute('action'), {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Add new option to select element
                            const option = document.createElement('option');
                            option.value = data.id;
                            option.textContent = data.name;
                            managementCompanySelect.appendChild(option);
                            
                            // Select the new option
                            managementCompanySelect.value = data.id;
                            
                            // Close the modal
                            modal.hide();
                            
                            // Reset the form
                            modalForm.reset();
                        } else {
                            // Display errors
                            alert('Error: ' + data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred. Please try again.');
                    });
                });
            }
        }
    }
});