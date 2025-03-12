document.addEventListener('DOMContentLoaded', function() {
    // Retrieve selectedTaxYear from the global variable or URL if not set
    var selectedTaxYear = window.selectedTaxYear || "";
    if (!selectedTaxYear) {
        const params = new URLSearchParams(window.location.search);
        selectedTaxYear = params.get('tax_year') || "";
    }
    if (selectedTaxYear) {
        // Find the first table row with the matching tax year
        const row = document.querySelector("tr[data-tax-year='" + selectedTaxYear + "']");
        if (row) {
            row.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }

    // Existing code for file input and modal issues
    document.querySelectorAll('[id^="uploadModal"] input[type="file"]').forEach(input => {
        input.addEventListener('change', function() {
            console.log('File selected:', this.files[0]?.name || 'No file selected');
        });
    });

    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
});
