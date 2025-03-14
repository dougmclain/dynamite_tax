// static/js/filing_status_filter.js

document.addEventListener('DOMContentLoaded', function() {
    // Filter for showing/hiding associations not being filed
    const showAllCheckbox = document.getElementById('show-all-associations');
    const notFilingRows = document.querySelectorAll('tr.not-filing');

    if (showAllCheckbox && notFilingRows.length > 0) {
        showAllCheckbox.addEventListener('change', function() {
            notFilingRows.forEach(row => {
                row.style.display = this.checked ? 'table-row' : 'none';
            });
        });
    }
});