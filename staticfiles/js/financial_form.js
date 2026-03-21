function formatCurrency(input) {
    let value = input.value.replace(/[^\d.]/g, '');
    let num = Math.round(parseFloat(value));
    if (isNaN(num) || num <= 0) {
        input.value = '$0';
        return;
    }
    input.value = '$' + num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function unformatCurrency(input) {
    let value = input.value.replace(/[^\d.]/g, '');
    let num = Math.round(parseFloat(value));
    input.value = isNaN(num) ? '0' : String(num);
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
            this.select();
        });
    });

    document.querySelector('form').addEventListener('submit', function() {
        dollarInputs.forEach(function(input) {
            unformatCurrency(input);
        });
    });
});
