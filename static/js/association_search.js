document.addEventListener('DOMContentLoaded', function() {
    // Make the association dropdown searchable
    const associationSelects = document.querySelectorAll('select[name="association_id"], select[id="association_select"], select[id="id_association"]');
    
    associationSelects.forEach(function(associationSelect) {
        if (!associationSelect) return;
        
        // Check if this select already has a search input above it
        const parentElement = associationSelect.parentNode;
        if (parentElement.querySelector('input[type="text"]')) {
            return; // Skip if there's already a search input
        }
        
        // Create wrapper and search input
        const wrapper = document.createElement('div');
        wrapper.className = 'select-search-wrapper position-relative';
        
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'form-control mb-1';
        searchInput.placeholder = 'Type to search associations...';
        
        // Insert the wrapper and search input before the select
        associationSelect.parentNode.insertBefore(wrapper, associationSelect);
        wrapper.appendChild(searchInput);
        wrapper.appendChild(associationSelect);
        
        // Store original options for filtering
        const originalOptions = Array.from(associationSelect.options);
        
        // Filter options as user types
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            // Keep the first option (placeholder) and filter the rest
            while (associationSelect.options.length > 1) {
                associationSelect.remove(1);
            }
            
            // Filter and add matching options
            originalOptions.forEach(function(option, index) {
                if (index === 0 || option.text.toLowerCase().includes(searchTerm)) {
                    associationSelect.add(option.cloneNode(true));
                }
            });
            
            // If we have exactly one match besides the placeholder, select it
            if (associationSelect.options.length === 2 && searchTerm) {
                associationSelect.selectedIndex = 1;
            }
        });
        
        // Clear search on select change
        associationSelect.addEventListener('change', function() {
            if (this.selectedIndex > 0) {
                searchInput.value = '';
            }
        });
    });
});