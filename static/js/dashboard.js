document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('associationTable');
    const headers = table.querySelectorAll('th.sortable');
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const sortBy = header.getAttribute('data-sort');
            const isAscending = header.classList.contains('asc');
            
            headers.forEach(h => h.classList.remove('asc', 'desc'));
            header.classList.toggle('asc', !isAscending);
            header.classList.toggle('desc', isAscending);

            const sortedRows = Array.from(rows).sort((a, b) => {
                let aValue = a.querySelector(`td[data-${sortBy}]`).getAttribute(`data-${sortBy}`);
                let bValue = b.querySelector(`td[data-${sortBy}]`).getAttribute(`data-${sortBy}`);

                if (sortBy === 'name') {
                    return isAscending ? bValue.localeCompare(aValue) : aValue.localeCompare(bValue);
                } else if (sortBy === 'extension' || sortBy === 'return') {
                    // For date comparisons
                    return isAscending ? bValue.localeCompare(aValue) : aValue.localeCompare(bValue);
                } else {
                    return isAscending ? bValue - aValue : aValue - bValue;
                }
            });

            tbody.innerHTML = '';
            sortedRows.forEach(row => tbody.appendChild(row));
        });
    });

    rows.forEach(row => {
        row.addEventListener('click', function(event) {
            // Don't navigate if clicking on a button, link, dropdown or their children
            if (event.target.closest('a') || 
                event.target.closest('button') || 
                event.target.closest('.btn-group') || 
                event.target.closest('.dropdown-menu')) {
                // Don't do the default row navigation
                return;
            }
            
            // Otherwise navigate to the row's href
            window.location.href = this.dataset.href;
        });
    });
});