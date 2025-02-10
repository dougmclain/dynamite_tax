function formatCurrency(input) {
    let value = input.value.replace(/[^\d.]/g, '');
    value = parseFloat(value).toFixed(2);
    if (!isNaN(value)) {
        input.value = '$' + value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
}

function unformatCurrency(input) {
    input.value = input.value.replace(/[^\d.]/g, '');
}

document.addEventListener('DOMContentLoaded', function() {
    const dollarInputs = document.querySelectorAll('.dollar-input');
    dollarInputs.forEach(function(input) {
        // Format initial value
        const originalValue = input.getAttribute('data-original-value');
        if (originalValue) {
            input.value = originalValue;
            formatCurrency(input);
        }

        input.addEventListener('blur', function() {
            formatCurrency(this);
        });

        input.addEventListener('focus', function() {
            unformatCurrency(this);
        });
    });

    document.querySelector('form').addEventListener('submit', function(e) {
        dollarInputs.forEach(function(input) {
            unformatCurrency(input);
        });
    });
});