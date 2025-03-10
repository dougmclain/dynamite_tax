document.addEventListener('DOMContentLoaded', function() {
    const associationSelect = document.getElementById('id_association');
    const taxYearSelect = document.getElementById('id_tax_year');

    console.log('DOM fully loaded');
    console.log('Association select:', associationSelect);
    console.log('Tax year select:', taxYearSelect);

    if (associationSelect && taxYearSelect) {
        // Function to load tax years for a given association
        const loadTaxYears = function(associationId, callback) {
            console.log('Loading tax years for association:', associationId);
            fetch(`/form-1120h/?association_id=${associationId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data);
                taxYearSelect.innerHTML = '<option value="">Select a year</option>';
                if (data.length > 0) {
                    data.forEach(year => {
                        const option = document.createElement('option');
                        option.value = year;
                        option.textContent = year;
                        taxYearSelect.appendChild(option);
                    });
                    taxYearSelect.disabled = false;
                    console.log('Tax year select populated and enabled');
                    
                    // If a callback is provided, execute it after populating tax years
                    if (typeof callback === 'function') {
                        callback();
                    }
                } else {
                    console.log('No tax years received for this association');
                    taxYearSelect.innerHTML = '<option value="">No tax years available</option>';
                    taxYearSelect.disabled = true;
                }
            })
            .catch(error => {
                console.error('Error fetching tax years:', error);
                taxYearSelect.innerHTML = '<option value="">Error loading years</option>';
                taxYearSelect.disabled = true;
            });
        };

        // Add change event listener
        associationSelect.addEventListener('change', function() {
            const associationId = this.value;
            console.log('Association changed. Selected ID:', associationId);

            if (associationId) {
                loadTaxYears(associationId);
            } else {
                console.log('No association selected');
                taxYearSelect.innerHTML = '<option value="">Select an association first</option>';
                taxYearSelect.disabled = true;
            }
        });

        console.log('Change event listener added to association select');
        
        // When page loads, if association is already selected, load its tax years
        // and then try to select the previously selected tax year
        if (associationSelect.value) {
            console.log('Association already selected on page load:', associationSelect.value);
            // Get the initially selected tax year value if it exists
            const initialSelectedTaxYear = taxYearSelect.value;
            console.log('Initial tax year value:', initialSelectedTaxYear);
            
            // Load tax years and then try to select the previous value
            loadTaxYears(associationSelect.value, function() {
                if (initialSelectedTaxYear) {
                    // Try to select the previously selected tax year
                    for (let i = 0; i < taxYearSelect.options.length; i++) {
                        if (taxYearSelect.options[i].value === initialSelectedTaxYear) {
                            taxYearSelect.selectedIndex = i;
                            console.log('Restored previous tax year selection:', initialSelectedTaxYear);
                            break;
                        }
                    }
                }
            });
        }
    } else {
        console.error('Association or tax year select not found in the DOM');
    }
});