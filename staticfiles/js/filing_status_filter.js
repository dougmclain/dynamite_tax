// static/js/filing_status_filter.js

document.addEventListener('DOMContentLoaded', function() {
    // Filter for showing/hiding associations not being filed
    const showAllCheckbox = document.getElementById('show-all-associations');
    const notFilingRows = document.querySelectorAll('tr.not-filing');

    if (showAllCheckbox && notFilingRows.length > 0) {
        // Set initial state based on localStorage preference
        const showAll = localStorage.getItem('showAllAssociations') !== 'false';
        showAllCheckbox.checked = showAll;
        
        // Apply initial state
        notFilingRows.forEach(row => {
            row.style.display = showAll ? 'table-row' : 'none';
        });
        
        // Handle checkbox changes
        showAllCheckbox.addEventListener('change', function() {
            const showAll = this.checked;
            
            // Save preference
            localStorage.setItem('showAllAssociations', showAll);
            
            // Update display
            notFilingRows.forEach(row => {
                row.style.display = showAll ? 'table-row' : 'none';
            });
        });
    }
    
    // Auto-submit form when filter values change
    const taxYearSelect = document.getElementById('tax_year');
    const managementCompanySelect = document.getElementById('management_company');
    
    if (taxYearSelect) {
        taxYearSelect.addEventListener('change', function() {
            this.form.submit();
        });
    }
    
    if (managementCompanySelect) {
        managementCompanySelect.addEventListener('change', function() {
            this.form.submit();
        });
    }
});