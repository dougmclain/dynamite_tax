document.addEventListener("DOMContentLoaded", function() {
    const dropZone = document.querySelector(".drop-zone");
    const fileInput = document.querySelector(".drop-zone__input");
    const fileInfo = document.getElementById("fileInfo");
    const fileNameSpan = document.getElementById("fileName");
    
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) {
            updateThumbnail(dropZone, fileInput.files[0]);
            showFileInfo(fileInput.files[0]);
        }
    });

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
            fileInput.files = e.dataTransfer.files;
            updateThumbnail(dropZone, e.dataTransfer.files[0]);
            showFileInfo(e.dataTransfer.files[0]);
        }
        
        dropZone.classList.remove("drop-zone--over");
    });

    function updateThumbnail(dropZone, file) {
        // First time - remove the prompt
        if (dropZone.querySelector(".drop-zone__prompt")) {
            dropZone.querySelector(".drop-zone__prompt").remove();
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
            thumbnailElement.style.backgroundImage = "url('/static/images/pdf-icon.png')";
        } else {
            thumbnailElement.style.backgroundImage = null;
        }
        
        // Show the file name
        thumbnailElement.dataset.label = file.name;
    }
    
    function showFileInfo(file) {
        fileNameSpan.textContent = file.name;
        fileInfo.classList.remove("d-none");
    }
    
    // Form validation before submit
    const uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", (e) => {
            if (!fileInput.files.length) {
                e.preventDefault();
                alert("Please select a file to upload.");
            }
        });
    }
});