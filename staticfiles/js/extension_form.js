document.addEventListener('DOMContentLoaded', function() {
    const associationSelect = document.getElementById('association_select');
    const taxYearSelect = document.getElementById('tax_year_select');
    const calculateBtn = document.getElementById('calculate_btn');
    const form = document.getElementById('extension_form');

    // Handle association selection and tax year loading
    if (associationSelect && taxYearSelect) {
        // Function to load tax years for a given association
        const loadTaxYears = function(associationId, callback) {
            if (associationId) {
                fetch(`/extension-form/?association_id=${associationId}`, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    taxYearSelect.innerHTML = '<option value="">Select a year</option>';
                    if (data.length > 0) {
                        data.forEach(year => {
                            const option = document.createElement('option');
                            option.value = year;
                            option.textContent = year;
                            taxYearSelect.appendChild(option);
                        });
                        taxYearSelect.disabled = false;
                        
                        // If a callback is provided, execute it after populating tax years
                        if (typeof callback === 'function') {
                            callback();
                        }
                    } else {
                        taxYearSelect.innerHTML = '<option value="">No tax years available</option>';
                        taxYearSelect.disabled = true;
                    }
                })
                .catch(error => {
                    console.error('Error fetching tax years:', error);
                    taxYearSelect.innerHTML = '<option value="">Error loading years</option>';
                    taxYearSelect.disabled = true;
                });
            } else {
                taxYearSelect.innerHTML = '<option value="">Select an association first</option>';
                taxYearSelect.disabled = true;
            }
        };

        // Add change event listener to association select
        associationSelect.addEventListener('change', function() {
            const associationId = this.value;
            loadTaxYears(associationId);
        });

        // Handle Start Extension button
        calculateBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const associationId = associationSelect.value;
            const taxYear = taxYearSelect.value;

            if (associationId && taxYear) {
                window.location.href = `/extension-form/?association_id=${associationId}&tax_year=${taxYear}`;
            } else {
                alert('Please select both an association and a tax year.');
            }
        });
        
        // When page loads, if association is already selected, load its tax years
        // and try to select the previously selected tax year if available
        if (associationSelect.value) {
            // Store the current tax year value if it exists
            const currentTaxYear = taxYearSelect.dataset.selectedYear || '';
            
            loadTaxYears(associationSelect.value, function() {
                if (currentTaxYear) {
                    // Try to select the previously selected tax year
                    for (let i = 0; i < taxYearSelect.options.length; i++) {
                        if (taxYearSelect.options[i].value === currentTaxYear) {
                            taxYearSelect.selectedIndex = i;
                            break;
                        }
                    }
                }
            });
        }
    }

    // Handle Balance Due Calculation
    const updateBalanceDue = function() {
        const tentativeTaxInput = document.querySelector('input[name="tentative_tax"]');
        const totalPaymentsInput = document.querySelector('input[name="total_payments"]');
        const balanceDueSpan = document.querySelector('#balanceDue span');

        if (tentativeTaxInput && totalPaymentsInput && balanceDueSpan) {
            let tentativeTax = parseFloat(tentativeTaxInput.value) || 0;
            let totalPayments = parseFloat(totalPaymentsInput.value) || 0;
            let balanceDue = Math.max(0, tentativeTax - totalPayments);
            
            balanceDueSpan.textContent = balanceDue.toFixed(2);
        }
    };

    // Add event listeners for real-time balance calculation
    const dollarInputs = document.querySelectorAll('input[name="tentative_tax"], input[name="total_payments"]');
    dollarInputs.forEach(input => {
        input.addEventListener('input', updateBalanceDue);
    });

    // Initialize balance calculation
    updateBalanceDue();
});