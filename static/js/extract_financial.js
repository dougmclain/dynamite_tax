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

    // Store AI-extracted values for correction tracking
    var aiExtractedValues = {};
    var managementCompanyId = null;

    function onFileSelected() {
        extractBtn.disabled = !pdfInput.files.length;
        // Reset status when new file selected
        if (pdfInput.files.length) {
            statusDiv.classList.add('d-none');
        }
    }

    // Enable button when a file is selected (native file dialog)
    pdfInput.addEventListener('change', onFileSelected);

    // Also listen on the drop zone for drop events (backup in case change doesn't fire)
    var dropZone = document.getElementById('aiPdfDropZone');
    if (dropZone) {
        dropZone.addEventListener('drop', function() {
            // Small delay to let drag_drop_upload.js set fileInput.files first
            setTimeout(onFileSelected, 50);
        });
    }

    extractBtn.addEventListener('click', function() {
        if (!pdfInput.files.length) return;

        var file = pdfInput.files[0];
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showError('Please select a PDF file.');
            return;
        }

        // Build FormData
        var formData = new FormData();
        formData.append('pdf_file', file);

        // Get association_id and tax_year from the form
        var associationInput = document.querySelector('input[name="association"]');
        var taxYearInput = document.querySelector('input[name="tax_year"]');
        if (associationInput) formData.append('association_id', associationInput.value);
        if (taxYearInput) formData.append('tax_year', taxYearInput.value);

        // CSRF token from existing form
        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

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
                // Store management company ID for correction tracking
                managementCompanyId = result.data.management_company_id;

                // Store the AI-extracted values before populating the form
                aiExtractedValues = JSON.parse(JSON.stringify(result.data.data));

                var count = populateFormFields(result.data.data);
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

    // Intercept form submission to save corrections
    var financialForm = document.querySelector('form[method="post"]');
    if (financialForm) {
        financialForm.addEventListener('submit', function() {
            if (!managementCompanyId || Object.keys(aiExtractedValues).length === 0) return;

            var taxYearInput = document.querySelector('input[name="tax_year"]');
            var taxYear = taxYearInput ? taxYearInput.value : '';
            var corrections = [];

            for (var fieldName in aiExtractedValues) {
                var input = document.getElementById('id_' + fieldName);
                if (!input) continue;

                var aiVal = aiExtractedValues[fieldName];
                var currentVal;

                if (typeof aiVal === 'number') {
                    // Parse the current value, stripping dollar formatting
                    currentVal = parseInt(input.value.replace(/[^\d]/g, '')) || 0;
                    if (currentVal !== aiVal) {
                        corrections.push({
                            field_name: fieldName,
                            ai_value: String(aiVal),
                            corrected_value: String(currentVal)
                        });
                    }
                } else if (typeof aiVal === 'string') {
                    currentVal = input.value;
                    if (currentVal !== aiVal) {
                        corrections.push({
                            field_name: fieldName,
                            ai_value: aiVal,
                            corrected_value: currentVal
                        });
                    }
                }
            }

            if (corrections.length === 0) return;

            // Send corrections asynchronously (fire-and-forget, don't block form submission)
            var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            fetch('/save-extraction-corrections/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    management_company_id: managementCompanyId,
                    tax_year: taxYear,
                    corrections: corrections
                }),
            }).catch(function(err) {
                console.error('Failed to save extraction corrections:', err);
            });
        });
    }

    function populateFormFields(data) {
        var count = 0;
        for (var fieldName in data) {
            var value = data[fieldName];
            var input = document.getElementById('id_' + fieldName);
            if (!input) continue;

            if (typeof value === 'number') {
                // Only skip if user has a meaningful non-zero value and AI returned 0
                var currentVal = parseInt(input.value.replace(/[^\d]/g, '')) || 0;
                if (value === 0 && currentVal > 0) continue;

                input.value = String(Math.round(value));
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
