document.addEventListener('DOMContentLoaded', function() {
    const pdfInput = document.getElementById('ai_pdf_file');
    const extractBtn = document.getElementById('ai-extract-btn');
    const statusDiv = document.getElementById('ai-extract-status');
    const loadingDiv = document.getElementById('ai-extract-loading');
    const successDiv = document.getElementById('ai-extract-success');
    const errorDiv = document.getElementById('ai-extract-error');
    const fieldsFilled = document.getElementById('ai-fields-filled');
    const errorMessage = document.getElementById('ai-error-message');

    if (!pdfInput || !extractBtn) return;

    // Enable button when a file is selected
    pdfInput.addEventListener('change', function() {
        extractBtn.disabled = !this.files.length;
        // Reset status when new file selected
        statusDiv.classList.add('d-none');
    });

    extractBtn.addEventListener('click', function() {
        if (!pdfInput.files.length) return;

        const file = pdfInput.files[0];
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showError('Please select a PDF file.');
            return;
        }

        // Build FormData
        const formData = new FormData();
        formData.append('pdf_file', file);

        // Get association_id and tax_year from the form
        const associationSelect = document.getElementById('id_association');
        const taxYearInput = document.getElementById('id_tax_year');
        if (associationSelect) formData.append('association_id', associationSelect.value);
        if (taxYearInput) formData.append('tax_year', taxYearInput.value);

        // CSRF token from existing form
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Show loading state
        showLoading();
        extractBtn.disabled = true;

        fetch('/extract-financial/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
        .then(function(response) {
            return response.json().then(function(data) {
                return {status: response.status, data: data};
            });
        })
        .then(function(result) {
            if (result.status === 200 && result.data.success) {
                const count = populateFormFields(result.data.data);
                showSuccess(count);
            } else {
                showError(result.data.error || 'Unknown error occurred.');
            }
        })
        .catch(function(error) {
            console.error('Extraction request failed:', error);
            showError('Network error. Please check your connection and try again.');
        })
        .finally(function() {
            extractBtn.disabled = !pdfInput.files.length;
        });
    });

    function populateFormFields(data) {
        let count = 0;
        for (const [fieldName, value] of Object.entries(data)) {
            const input = document.getElementById('id_' + fieldName);
            if (!input) continue;

            if (typeof value === 'number') {
                // Only skip if user has a meaningful non-zero value and AI returned 0
                const currentVal = parseInt(input.value.replace(/[^\d]/g, '')) || 0;
                if (value === 0 && currentVal > 0) continue;

                input.value = value;
                // Trigger dollar formatting from financial_form.js
                if (input.classList.contains('dollar-input')) {
                    formatCurrency(input);
                }
                if (value > 0) count++;
            } else if (typeof value === 'string' && value) {
                input.value = value;
                count++;
            }
        }
        return count;
    }

    function showLoading() {
        statusDiv.classList.remove('d-none');
        loadingDiv.classList.remove('d-none');
        successDiv.classList.add('d-none');
        errorDiv.classList.add('d-none');
    }

    function showSuccess(count) {
        loadingDiv.classList.add('d-none');
        successDiv.classList.remove('d-none');
        fieldsFilled.textContent = count;
    }

    function showError(msg) {
        statusDiv.classList.remove('d-none');
        loadingDiv.classList.add('d-none');
        errorDiv.classList.remove('d-none');
        errorMessage.textContent = msg;
    }
});
