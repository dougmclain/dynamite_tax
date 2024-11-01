document.addEventListener('DOMContentLoaded', function() {
    const associationSelect = document.getElementById('association_select');
    const taxYearSelect = document.getElementById('tax_year_select');
    const calculateBtn = document.getElementById('calculate_btn');

    console.log('DOM fully loaded');

    if (associationSelect && taxYearSelect) {
        associationSelect.addEventListener('change', function() {
            const associationId = this.value;
            console.log('Association changed. Selected ID:', associationId);

            if (associationId) {
                console.log('Fetching tax years for association:', associationId);
                fetch(`/extension-form/?association_id=${associationId}`, {
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
            } else {
                console.log('No association selected');
                taxYearSelect.innerHTML = '<option value="">Select an association first</option>';
                taxYearSelect.disabled = true;
            }
        });

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
    }

    // Handle dollar input formatting
    const dollarInputs = document.querySelectorAll('.dollar-input');
    dollarInputs.forEach(function(input) {
        // Format initial value
        const originalValue = input.getAttribute('data-original-value');
        if (originalValue) {
            input.value = originalValue;
            formatCurrency(input);
        }

        input.addEventListener('blur', function() {
            formatCurrency(this);
            updateBalanceDue();
        });

        input.addEventListener('focus', function() {
            unformatCurrency(this);
        });
    });

    // Update balance due calculation
    function updateBalanceDue() {
        const tentativeTaxInput = document.querySelector('input[name="tentative_tax"]');
        const totalPaymentsInput = document.querySelector('input[name="total_payments"]');
        const balanceDueSpan = document.querySelector('#balanceDue span');

        if (tentativeTaxInput && totalPaymentsInput && balanceDueSpan) {
            const tentativeTax = parseFloat(tentativeTaxInput.value.replace(/[^\d.]/g, '')) || 0;
            const totalPayments = parseFloat(totalPaymentsInput.value.replace(/[^\d.]/g, '')) || 0;
            const balanceDue = Math.max(0, tentativeTax - totalPayments);
            balanceDueSpan.textContent = balanceDue.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    }

    // Initialize balance due calculations
    const balanceDueInputs = document.querySelectorAll('input[name="tentative_tax"], input[name="total_payments"]');
    balanceDueInputs.forEach(input => {
        input.addEventListener('input', updateBalanceDue);
    });
    updateBalanceDue();

    function formatCurrency(input) {
        let value = input.value.replace(/[^\d.]/g, '');
        value = parseFloat(value).toFixed(2);
        if (!isNaN(value)) {
            input.value = '$' + value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
    }

    function unformatCurrency(input) {
        input.value = input.value.replace(/[^\d.]/g, '');
    }

    // Handle form submission
    const form = document.getElementById('extension_form');
    if (form) {
        form.addEventListener('submit', function(e) {
            dollarInputs.forEach(function(input) {
                unformatCurrency(input);
            });
        });
    }
});