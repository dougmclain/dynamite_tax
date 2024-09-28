document.addEventListener('DOMContentLoaded', function() {
    const associationSelect = document.getElementById('id_association');
    const taxYearSelect = document.getElementById('id_tax_year');

    console.log('DOM fully loaded');
    console.log('Association select:', associationSelect);
    console.log('Tax year select:', taxYearSelect);

    if (associationSelect && taxYearSelect) {
        associationSelect.addEventListener('change', function() {
            const associationId = this.value;
            console.log('Association changed. Selected ID:', associationId);

            if (associationId) {
                console.log('Fetching tax years for association:', associationId);
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

        console.log('Change event listener added to association select');
    } else {
        console.error('Association or tax year select not found in the DOM');
    }
});