document.addEventListener('DOMContentLoaded', function() {
    var filterSelects = document.querySelectorAll('#filter-row select');
    var tableRows = document.querySelectorAll('#associationTable tbody tr');
    var clearBtn = document.getElementById('clear-filters');

    function applyFilters() {
        var filters = {};
        filterSelects.forEach(function(select) {
            var key = select.getAttribute('data-filter');
            var val = select.value;
            if (val) filters[key] = val;
        });

        tableRows.forEach(function(row) {
            var show = true;
            for (var key in filters) {
                var rowVal = row.getAttribute('data-' + key);
                if (rowVal !== filters[key]) {
                    show = false;
                    break;
                }
            }
            row.style.display = show ? '' : 'none';
        });
    }

    if (filterSelects.length) {
        filterSelects.forEach(function(select) {
            select.addEventListener('change', applyFilters);
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            filterSelects.forEach(function(select) { select.value = ''; });
            applyFilters();
        });
    }

    // Auto-submit form when tax year or management company changes
    var taxYearSelect = document.getElementById('tax_year');
    var mgmtSelect = document.getElementById('management_company');
    if (taxYearSelect) taxYearSelect.addEventListener('change', function() { this.form.submit(); });
    if (mgmtSelect) mgmtSelect.addEventListener('change', function() { this.form.submit(); });
});
