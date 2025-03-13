document.addEventListener("DOMContentLoaded", function() {
    initializeDropZones();
});

function initializeDropZones() {
    // Find all drop zones on the page
    const dropZones = document.querySelectorAll(".drop-zone");
    
    if (!dropZones.length) return;

    dropZones.forEach(dropZone => {
        const fileInput = dropZone.querySelector(".drop-zone__input");
        if (!fileInput) return;
        
        const uniqueId = fileInput.id || Math.random().toString(36).substring(2, 15);
        
        // Click to open file dialog
        dropZone.addEventListener("click", () => {
            fileInput.click();
        });

        // Handle file selection
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length) {
                updateThumbnail(dropZone, fileInput.files[0]);
            }
        });

        // Handle drag events
        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("drop-zone--over");
        });

        ["dragleave", "dragend"].forEach((type) => {
            dropZone.addEventListener(type, () => {
                dropZone.classList.remove("drop-zone--over");
            });
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            
            if (e.dataTransfer.files.length) {
                // Only use the first file even if multiple were dropped
                fileInput.files = e.dataTransfer.files;
                updateThumbnail(dropZone, e.dataTransfer.files[0]);
            }
            
            dropZone.classList.remove("drop-zone--over");
        });
    });
}

function updateThumbnail(dropZone, file) {
    // First time - remove the prompt
    let promptElement = dropZone.querySelector(".drop-zone__prompt");
    if (promptElement) {
        promptElement.remove();
    }
    
    // First time - if there's no thumbnail element, create it
    let thumbnailElement = dropZone.querySelector(".drop-zone__thumb");
    if (!thumbnailElement) {
        thumbnailElement = document.createElement("div");
        thumbnailElement.classList.add("drop-zone__thumb");
        dropZone.appendChild(thumbnailElement);
    }

    // Show thumbnail for PDFs
    if (file.type === "application/pdf") {
        // Try to find a PDF icon in our static files
        const pdfIconPath = "/static/images/pdf-icon.png";
        thumbnailElement.style.backgroundImage = `url('${pdfIconPath}')`;
        thumbnailElement.style.backgroundSize = "contain";
        thumbnailElement.style.backgroundRepeat = "no-repeat";
        thumbnailElement.style.backgroundPosition = "center";
    } else {
        thumbnailElement.style.backgroundImage = null;
    }
    
    // Show the file name
    thumbnailElement.dataset.label = file.name;
}