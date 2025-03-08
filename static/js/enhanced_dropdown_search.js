// static/js/enhanced_dropdown_search.js
document.addEventListener('DOMContentLoaded', function() {
    // Find all select elements with the searchable class
    const searchableSelects = document.querySelectorAll('select.searchable');
    
    searchableSelects.forEach(function(select) {
      // Create a div container for our custom dropdown
      const container = document.createElement('div');
      container.className = 'custom-select-container';
      select.parentNode.insertBefore(container, select);
      container.appendChild(select);
      
      // Create search input
      const searchInput = document.createElement('input');
      searchInput.type = 'text';
      searchInput.className = 'form-control custom-select-search';
      searchInput.placeholder = 'Type to search...';
      container.insertBefore(searchInput, select);
      
      // Create dropdown for filtered options
      const dropdown = document.createElement('div');
      dropdown.className = 'custom-select-dropdown d-none';
      document.body.appendChild(dropdown); // Append to body instead to avoid stacking context issues
      
      // Store original options
      const originalOptions = Array.from(select.options);
      
      // Function to show/hide dropdown
      function toggleDropdown(show) {
        if (show) {
          // Position the dropdown under the input
          const inputRect = searchInput.getBoundingClientRect();
          dropdown.style.top = (inputRect.bottom + window.scrollY) + 'px';
          dropdown.style.left = (inputRect.left + window.scrollX) + 'px';
          dropdown.style.width = inputRect.width + 'px';
          
          dropdown.classList.remove('d-none');
        } else {
          dropdown.classList.add('d-none');
        }
      }
      
      // Function to render filtered options in dropdown
      function renderOptions(filter = '') {
        dropdown.innerHTML = '';
        
        const lowerFilter = filter.toLowerCase();
        let hasMatch = false;
        
        originalOptions.forEach(function(option) {
          if (option.text.toLowerCase().includes(lowerFilter)) {
            hasMatch = true;
            const item = document.createElement('div');
            item.className = 'custom-select-item';
            if (option.value === select.value) {
              item.classList.add('selected');
            }
            item.textContent = option.text;
            item.dataset.value = option.value;
            dropdown.appendChild(item);
            
            // Add click event to select the option
            item.addEventListener('click', function() {
              select.value = this.dataset.value;
              searchInput.value = this.textContent;
              toggleDropdown(false);
              // Trigger change event
              const event = new Event('change', { bubbles: true });
              select.dispatchEvent(event);
            });
          }
        });
        
        // Show message if no matches
        if (!hasMatch && filter) {
          const noMatch = document.createElement('div');
          noMatch.className = 'custom-select-no-results';
          noMatch.textContent = 'No matches found';
          dropdown.appendChild(noMatch);
        }
        
        // Show dropdown if we have filter text or matches
        toggleDropdown(filter || hasMatch);
      }
      
      // Initialize with selected value if any
      if (select.value) {
        const selectedOption = select.options[select.selectedIndex];
        if (selectedOption) {
          searchInput.value = selectedOption.text;
        }
      }
      
      // Add event listeners
      searchInput.addEventListener('focus', function() {
        renderOptions(this.value);
      });
      
      searchInput.addEventListener('input', function() {
        renderOptions(this.value);
      });
      
      searchInput.addEventListener('blur', function() {
        // Delay hiding dropdown to allow for option clicks
        setTimeout(() => toggleDropdown(false), 200);
      });
      
      // Hide the original select
      select.style.display = 'none';
    });
  });