document.addEventListener('DOMContentLoaded', function() {
    var filterMenus = document.querySelectorAll('#filter-row .dropdown-menu');
    var tableRows = document.querySelectorAll('#associationTable tbody tr');
    var clearBtn = document.getElementById('clear-filters');

    function getActiveFilters() {
        var filters = {};
        filterMenus.forEach(function(menu) {
            var key = menu.getAttribute('data-filter');
            var checked = menu.querySelectorAll('input[type="checkbox"]:checked');
            if (checked.length > 0) {
                filters[key] = [];
                checked.forEach(function(cb) { filters[key].push(cb.value); });
            }
        });
        return filters;
    }

    function applyFilters() {
        var filters = getActiveFilters();

        tableRows.forEach(function(row) {
            var show = true;
            for (var key in filters) {
                var rowVal = row.getAttribute('data-' + key);
                if (filters[key].indexOf(rowVal) === -1) {
                    show = false;
                    break;
                }
            }
            row.style.display = show ? '' : 'none';
        });

        // Update button labels to show active filter count
        filterMenus.forEach(function(menu) {
            var btn = menu.previousElementSibling;
            var label = btn.textContent.replace(/ \(\d+\)$/, '');
            var checked = menu.querySelectorAll('input[type="checkbox"]:checked');
            var total = menu.querySelectorAll('input[type="checkbox"]');
            if (checked.length > 0 && checked.length < total.length) {
                btn.textContent = label + ' (' + checked.length + ')';
                btn.classList.remove('btn-outline-secondary');
                btn.classList.add('btn-primary');
            } else {
                btn.textContent = label;
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline-secondary');
            }
        });
    }

    // Listen for checkbox changes inside filter dropdowns
    filterMenus.forEach(function(menu) {
        menu.addEventListener('change', applyFilters);
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            filterMenus.forEach(function(menu) {
                menu.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
                    cb.checked = false;
                });
            });
            applyFilters();
        });
    }

    // Apply initial filters (Filing Status has "Will File" checked by default)
    applyFilters();

    // Auto-submit form when tax year or management company changes
    var taxYearSelect = document.getElementById('tax_year');
    var mgmtSelect = document.getElementById('management_company');
    if (taxYearSelect) taxYearSelect.addEventListener('change', function() { this.form.submit(); });
    if (mgmtSelect) mgmtSelect.addEventListener('change', function() { this.form.submit(); });
});
