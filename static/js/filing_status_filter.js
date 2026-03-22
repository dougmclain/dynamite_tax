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

        updateSummaryCounts();
    }

    function updateSummaryCounts() {
        var visible = document.querySelectorAll('#associationTable tbody tr:not([style*="display: none"])');
        var total = 0, toFile = 0, notFiling = 0;
        var filed = 0, sent = 0, reviewed = 0, unfiled = 0;
        var signed = 0, engTotal = 0;
        var paid = 0, invoiced = 0, toInvoice = 0;

        visible.forEach(function(row) {
            total++;
            var fs = row.getAttribute('data-filing-status');
            if (fs === 'will_file') {
                toFile++;
                // Return status counts (only for "will file" associations)
                if (row.getAttribute('data-filed') === 'filed') filed++;
                else unfiled++;
                if (row.getAttribute('data-sent') === 'sent') sent++;
                if (row.getAttribute('data-reviewed') === 'reviewed') reviewed++;
                // Engagement
                if (row.getAttribute('data-engagement') === 'signed') signed++;
                engTotal++;
                // Invoice
                var inv = row.getAttribute('data-invoice');
                if (inv === 'paid') paid++;
                else if (inv === 'invoiced') invoiced++;
                else if (inv === 'not_invoiced') toInvoice++;
            } else {
                notFiling++;
            }
        });

        var el = document.getElementById.bind(document);
        if (el('summary-total')) el('summary-total').textContent = total;
        if (el('summary-to-file')) el('summary-to-file').textContent = toFile;
        if (el('summary-not-filing')) el('summary-not-filing').textContent = notFiling;
        if (el('summary-filed')) el('summary-filed').textContent = filed;
        if (el('summary-sent')) el('summary-sent').textContent = sent;
        if (el('summary-reviewed')) el('summary-reviewed').textContent = reviewed;
        if (el('summary-unfiled')) el('summary-unfiled').textContent = unfiled;
        if (el('summary-signed')) el('summary-signed').textContent = signed;
        if (el('summary-needed')) el('summary-needed').textContent = Math.max(0, toFile - signed);
        if (el('summary-paid')) el('summary-paid').textContent = paid;
        if (el('summary-invoiced')) el('summary-invoiced').textContent = invoiced;
        if (el('summary-to-invoice')) el('summary-to-invoice').textContent = toInvoice;
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
