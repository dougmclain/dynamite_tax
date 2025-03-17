// static/js/pdf_cache_buster.js

document.addEventListener('DOMContentLoaded', function() {
    // Force reload of PDFs by adding a timestamp to any PDF links
    const pdfLinks = document.querySelectorAll('a[href$=".pdf"], a[href*=".pdf?"]');
    pdfLinks.forEach(link => {
        const currentHref = link.getAttribute('href');
        // Only add timestamp if not already present
        if (!currentHref.includes('?v=') && !currentHref.includes('&v=')) {
            const timestamp = new Date().getTime();
            if (currentHref.includes('?')) {
                // If URL already has query parameters, append with &
                link.setAttribute('href', `${currentHref}&v=${timestamp}`);
            } else {
                // Otherwise start a new query string with ?
                link.setAttribute('href', `${currentHref}?v=${timestamp}`);
            }
        }
    });
});